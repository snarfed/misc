/**
 * mockprpl
 * (formerly nullprpl)
 *
 * http://snarfed.org/space/gaim+mock+protocol+plugin
 * Copyright (C) 2004-2007, Ryan Barrett <mockprpl@ryanb.org>
 *
 * Mockprpl is a mock protocol plugin for Gaim. You can create accounts with
 * it, sign on and off, add buddies, and send and receive IMs, all without
 * connecting to a server!
 * 
 * Beyond that basic functionality, mockprpl supports presence and
 * away/available messages, offline messages, user info, typing notification,
 * privacy allow/block lists, chat rooms, whispering, room lists, and protocol
 * icons and emblems. Notable missing features are file transfer and account
 * registration and authentication.
 * 
 * Mockprpl is intended as an example of how to write a gaim protocol plugin.
 * It doesn't contain networking code or an event loop, but it does
 * demonstrate how to use the Gaim API to do pretty much everything a prpl
 * might need to do.
 * 
 * Mockprpl is also a useful tool for hacking on gaim itself. It's a
 * full-featured protocol plugin, but doesn't depend on an external server, so
 * it's a quick and easy way to exercise gaim and test new code. It also
 * allows you to work on gaim while you're disconnected.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include <assert.h>
#include <stdarg.h>
#include <string.h>
#include <time.h>

#include <glib.h>

#define GAIM_PLUGINS
#include "gaim/account.h"
#include "gaim/accountopt.h"
#include "gaim/blist.h"
#include "gaim/cmds.h"
#include "gaim/conversation.h"
#include "gaim/connection.h"
#include "gaim/debug.h"
#include "gaim/notify.h"
#include "gaim/privacy.h"
#include "gaim/prpl.h"
#include "gaim/roomlist.h"
#include "gaim/status.h"
#include "gaim/util.h"
#include "gaim/version.h"


#define MOCKPRPL_ID "prpl-mock"
static GaimPlugin *_mock_protocol = NULL;

#define MOCK_STATUS_ONLINE   "online"
#define MOCK_STATUS_AWAY     "away"
#define MOCK_STATUS_OFFLINE  "offline"

/* stolen from gaim's internal.h */
#ifdef ENABLE_NLS
#  include <locale.h>
#  include <libintl.h>
#  define _(String) ((const char *)gettext(String))
#else
#  include <locale.h>
#  ifndef _
#    define _(String) ((const char *)String)
#  endif
#endif

typedef void (*GcFunc)(GaimConnection *from,
                       GaimConnection *to,
                       gpointer userdata);

typedef struct {
  GcFunc fn;
  GaimConnection *from;
  gpointer userdata;
} GcFuncData;

/*
 * stores offline messages that haven't been delivered yet. maps username
 * (char *) to GList * of GOfflineMessages. initialized in mockprpl_init.
 */
GHashTable* goffline_messages = NULL;

typedef struct {
  char *from;
  char *message;
  time_t mtime;
  GaimMessageFlags flags;
} GOfflineMessage;

/*
 * helpers
 */
static GaimConnection *get_mockprpl_gc(const char *username) {
  GaimAccount *acct = gaim_accounts_find(username, MOCKPRPL_ID);
  if (acct && gaim_account_is_connected(acct))
    return acct->gc;
  else
    return NULL;
}

static void call_if_mockprpl(gpointer data, gpointer userdata) {
  GaimConnection *gc = (GaimConnection *)(data);
  GcFuncData *gcfdata = (GcFuncData *)userdata;

  if (!strcmp(gc->account->protocol_id, MOCKPRPL_ID))
    gcfdata->fn(gcfdata->from, gc, gcfdata->userdata);
}

static void foreach_mockprpl_gc(GcFunc fn, GaimConnection *from,
                                gpointer userdata) {
  GcFuncData gcfdata = { .fn = fn,
                         .from = from,
                         .userdata = userdata };
  g_list_foreach(gaim_connections_get_all(), call_if_mockprpl,
                 (gpointer)&gcfdata);
}


typedef void(*ChatFunc)(GaimConvChat *from, GaimConvChat *to,
                        int id, const char *room, gpointer userdata);

typedef struct {
  ChatFunc fn;
  GaimConvChat *from_chat;
  gpointer userdata;
} ChatFuncData;

static void call_chat_func(gpointer data, gpointer userdata) {
  GaimConnection *to = (GaimConnection *)data;
  ChatFuncData *cfdata = (ChatFuncData *)userdata;

  int id = cfdata->from_chat->id;
  GaimConversation *conv = gaim_find_chat(to, id);
  if (conv) {
    GaimConvChat *chat = gaim_conversation_get_chat_data(conv);
    cfdata->fn(cfdata->from_chat, chat, id, conv->name, cfdata->userdata);
  }
}

static void foreach_gc_in_chat(ChatFunc fn, GaimConnection *from,
                               int id, gpointer userdata) {
  GaimConversation *conv = gaim_find_chat(from, id);
  ChatFuncData cfdata = { .fn = fn,
                          .from_chat = gaim_conversation_get_chat_data(conv),
                          .userdata = userdata };

  g_list_foreach(gaim_connections_get_all(), call_chat_func,
                 (gpointer)&cfdata);
}


static void discover_status(GaimConnection *from, GaimConnection *to,
                            gpointer userdata) {
  char *from_username = from->account->username;
  char *to_username = to->account->username;

  if (gaim_find_buddy(from->account, to_username)) {
    GaimStatus *status = gaim_account_get_active_status(to->account);
    const char *status_id = gaim_status_get_id(status);
    assert(!strcmp(status_id, MOCK_STATUS_ONLINE) ||
           !strcmp(status_id, MOCK_STATUS_AWAY)   ||
           !strcmp(status_id, MOCK_STATUS_OFFLINE));

    const char *message = gaim_status_get_attr_string(status, "message");
    gaim_debug_info("mockprpl", "%s sees that %s is %s: %s\n", from_username,
                    to_username, status_id, message);
    
    gaim_prpl_got_user_status(from->account, to_username, status_id,
                              (message) ? "message" : NULL, message, NULL);
  }
}

static void report_status_change(GaimConnection *from, GaimConnection *to,
                                 gpointer userdata) {
  gaim_debug_info("mockprpl", "notifying %s that %s changed status\n",
                  to->account->username, from->account->username);
  discover_status(to, from, NULL);
}


/* 
 * UI callbacks
 */
static void mockprpl_input_user_info(GaimPluginAction *action)
{
  GaimConnection *gc = (GaimConnection *)action->context;
  GaimAccount *acct = gaim_connection_get_account(gc);
  gaim_debug_info("mockprpl", "showing 'Set User Info' dialog for %s\n",
                  acct->username);

  gaim_account_request_change_user_info(acct);
}

/* this is set to the actions member of the GaimPluginInfo struct at the
 * bottom.
 */
static GList *mockprpl_actions(GaimPlugin *plugin, gpointer context)
{
  GaimPluginAction *action = gaim_plugin_action_new(_("Set User Info..."),
                                                    mockprpl_input_user_info);
  return g_list_append(NULL, action);
}


/*
 * prpl functions
 */
static const char *mockprpl_list_icon(GaimAccount *acct, GaimBuddy *buddy)
{
  /* shamelessly steal (er, borrow) the meanwhile protocol icon. it's cute! */
  return "meanwhile";
}

static void mockprpl_list_emblems(GaimBuddy *buddy, const char **se,
                                  const char **sw, const char **nw,
                                  const char **ne)
{
  if (get_mockprpl_gc(buddy->name)) {
    GaimPresence *presence = gaim_buddy_get_presence(buddy);
    GaimStatus *status = gaim_presence_get_active_status(presence);
    *se = gaim_status_get_name(status);
  } else {
    *se = "offline";
  }

  gaim_debug_info("mockprpl", "using emblem %s for %s's buddy %s\n",
                  *se, buddy->account->username, buddy->name);
}

static char *mockprpl_status_text(GaimBuddy *buddy) {
  gaim_debug_info("mockprpl", "getting %s's status text for %s\n",
                  buddy->name, buddy->account->username);

  if (gaim_find_buddy(buddy->account, buddy->name)) {
    GaimPresence *presence = gaim_buddy_get_presence(buddy);
    GaimStatus *status = gaim_presence_get_active_status(presence);
    const char *name = gaim_status_get_name(status);
    const char *message = gaim_status_get_attr_string(status, "message");

    char *text;
    if (message && strlen(message) > 0)
      text = g_strdup_printf("%s: %s", name, message);
    else
      text = g_strdup(name);

    gaim_debug_info("mockprpl", "%s's status text is %s\n", buddy->name, text);
    return text;

  } else {
    gaim_debug_info("mockprpl", "...but %s is not logged in\n", buddy->name);
    return "Not logged in";
  }
}

static void mockprpl_tooltip_text(GaimBuddy *buddy, GString *str,
                                  gboolean full) {
  if (full)
    g_string_append_printf(str, "\nFull tooltip:");
  else
    g_string_append_printf(str, "\nShort tooltip:");
  
  GaimConnection *gc = get_mockprpl_gc(buddy->name);

  if (gc) {
    /* they're logged in */
    GaimPresence *presence = gaim_buddy_get_presence(buddy);
    GaimStatus *status = gaim_presence_get_active_status(presence);
    const char *msg = mockprpl_status_text(buddy);
    g_string_append_printf(str, _("\n%s: %s"),
                           gaim_status_get_name(status), msg);

    if (full) {
      g_string_append_printf(str, _("\nUser info: "));
      const char *user_info = gaim_account_get_user_info(gc->account);
      if (user_info)
        g_string_append_printf(str, user_info);
      else
        g_string_append_printf(str, _("No user info."));
    }

  } else {
    /* they're not logged in */
    g_string_append_printf(str, _("%s is not logged in."), buddy->name);
  }
    
  gaim_debug_info("mockprpl", "showing tooltip '%s'\n", str->str);
}

static GList *mockprpl_status_types(GaimAccount *acct)
{
  gaim_debug_info("mockprpl", "returning status types for %s: %s, %s, %s\n",
                  acct->username,
                  MOCK_STATUS_ONLINE, MOCK_STATUS_AWAY, MOCK_STATUS_OFFLINE);

  GList *types = NULL;
  GaimStatusType *type;

  type = gaim_status_type_new(GAIM_STATUS_AVAILABLE, MOCK_STATUS_ONLINE,
                              MOCK_STATUS_ONLINE, TRUE);
  gaim_status_type_add_attr(type, "message", _("Online"),
                            gaim_value_new(GAIM_TYPE_STRING));
  types = g_list_append(types, type);

  type = gaim_status_type_new(GAIM_STATUS_AWAY, MOCK_STATUS_AWAY,
                              MOCK_STATUS_AWAY, TRUE);
  gaim_status_type_add_attr(type, "message", _("Away"),
                            gaim_value_new(GAIM_TYPE_STRING));
  types = g_list_append(types, type);
  
  type = gaim_status_type_new(GAIM_STATUS_OFFLINE, MOCK_STATUS_OFFLINE,
                              MOCK_STATUS_OFFLINE, TRUE);
  gaim_status_type_add_attr(type, "message", _("Offline"),
                            gaim_value_new(GAIM_TYPE_STRING));
  types = g_list_append(types, type);

  return types;
}

static void blist_example_menu_item(GaimBlistNode *node, gpointer userdata) {
  gaim_debug_info("mockprpl", "example menu item clicked on user",
                  ((GaimBuddy *)node)->name);

  gaim_notify_info(NULL,                 /* plugin handle or GaimConnection */
                   _("Primary title"),
                   _("Secondary title"),
                   _("This is the callback for the mockprpl menu item."));
}

static GList *mockprpl_blist_node_menu(GaimBlistNode *node) {
  gaim_debug_info("mockprpl", "providing buddy list context menu item\n");

  if (GAIM_BLIST_NODE_IS_BUDDY(node)) {
    GaimMenuAction *action = gaim_menu_action_new(
      _("MockPrpl example menu item"),
      GAIM_CALLBACK(blist_example_menu_item),
      NULL,   /* userdata passed to the callback */
      NULL);  /* child menu items */
    return g_list_append(NULL, action);
  } else {
    return NULL;
  }
}

static GList *mockprpl_chat_info(GaimConnection *gc) {
  gaim_debug_info("mockprpl", "returning chat setting 'room'\n");

  struct proto_chat_entry *pce; /* defined in prpl.h */
  pce = g_new0(struct proto_chat_entry, 1);
  pce->label = _(_("Chat _room"));
  pce->identifier = "room";
  pce->required = TRUE;

  return g_list_append(NULL, pce);
}

static GHashTable *mockprpl_chat_info_defaults(GaimConnection *gc,
                                               const char *room) {
  gaim_debug_info("mockprpl", "returning chat default setting "
                  "'room' = 'default'\n");

  GHashTable *defaults;
  defaults = g_hash_table_new_full(g_str_hash, g_str_equal, NULL, g_free);
  g_hash_table_insert(defaults, "room", g_strdup("default"));
  return defaults;
}  

static void mockprpl_login(GaimAccount *acct)
{
  gaim_debug_info("mockprpl", "logging in %s\n", acct->username);

  GaimConnection *gc = gaim_account_get_connection(acct);
  gaim_connection_update_progress(gc, _("Connecting"),
                                  0,   /* which connection step this is */
                                  2);  /* total number of steps */

  gaim_connection_update_progress(gc, _("Connected"),
                                  1,   /* which connection step this is */
                                  2);  /* total number of steps */
  gaim_connection_set_state(gc, GAIM_CONNECTED);

  /* tell gaim about everyone on our buddy list who's connected */
  foreach_mockprpl_gc(discover_status, gc, NULL);

  /* notify other mockprpl accounts */
  foreach_mockprpl_gc(report_status_change, gc, NULL);

  /* fetch stored offline messages */
  gaim_debug_info("mockprpl", "checking for offline messages for %s\n",
                  acct->username);
  GList *offline_messages = g_hash_table_lookup(goffline_messages, 
                                                acct->username); 
  while (offline_messages) {
    GOfflineMessage *message = (GOfflineMessage *)offline_messages->data;
    gaim_debug_info("mockprpl", "delivering offline message to %s: %s\n",
                    acct->username, message->message);
    serv_got_im(gc, message->from, message->message, message->flags,
                message->mtime);
    offline_messages = g_list_next(offline_messages);

    g_free(message->from);
    g_free(message->message);
    g_free(message);
  }

  g_list_free(offline_messages);
  g_hash_table_remove(goffline_messages, &acct->username);
}

static void mockprpl_close(GaimConnection *gc)
{
  /* notify other mockprpl accounts */
  foreach_mockprpl_gc(report_status_change, gc, NULL);
}

static int mockprpl_send_im(GaimConnection *gc, const char *who,
                            const char *message, GaimMessageFlags flags)
{
  const char *from_username = gc->account->username;
  gaim_debug_info("mockprpl", "sending message from %s to %s: %s\n",
                  from_username, who, message);

  GaimMessageFlags receive_flags = ((flags & ~GAIM_MESSAGE_SEND)
                                    | GAIM_MESSAGE_RECV);

  /* is the sender blocked by the recipient's privacy settings? */
  GaimAccount *to_acct = gaim_accounts_find(who, MOCKPRPL_ID);
  if (!gaim_privacy_check(to_acct, gc->account->username)) {
    gaim_debug_info("mockprpl",
                    "discarding; %s is blocked by %s's privacy settings\n",
                    from_username, who);
    char *msg = g_strdup_printf(_("Your message was blocked by %s's privacy settings."),
                                who);
    gaim_conv_present_error(who, gc->account, msg);
    g_free(msg);
    return 0;
  }

  /* is the recipient online? */
  GaimConnection *to = get_mockprpl_gc(who);
  if (to) {  /* yes, send */
    serv_got_im(to, from_username, message, receive_flags, time(NULL));

  } else {  /* nope, store as an offline message */
    gaim_debug_info("mockprpl", "%s is offline, sending as offline message\n",
                    who);
    GOfflineMessage *offline_message = g_new0(GOfflineMessage, 1);
    offline_message->from = g_strdup(from_username);
    offline_message->message = g_strdup(message);
    offline_message->mtime = time(NULL);
    offline_message->flags = receive_flags;

    GList* messages = g_hash_table_lookup(goffline_messages, who);
    messages = g_list_append(messages, offline_message);
    g_hash_table_insert(goffline_messages, g_strdup(who), messages);
  }

   return 1;
}

static void mockprpl_set_info(GaimConnection *gc, const char *info) {
  gaim_debug_info("mockprpl", "setting %s's user info to %s\n",
                  gc->account->username, info);
}

static char *typing_state_to_string(GaimTypingState typing) {
  switch (typing) {
  case GAIM_NOT_TYPING:  return "is not typing";
  case GAIM_TYPING:      return "is typing";
  case GAIM_TYPED:       return "stopped typing momentarily";
  default:               return "unknown typing state";
  }
}

static void notify_typing(GaimConnection *from, GaimConnection *to,
                          gpointer typing) {
  char *from_username = from->account->username;
  char *action = typing_state_to_string((GaimTypingState)typing);
  gaim_debug_info("mockprpl", "notifying %s that %s %s\n",
                  to->account->username, from_username, action);

  serv_got_typing(to,
                  from_username,
                  0, /* if non-zero, a timeout in seconds after which to
                      * reset the typing status to GAIM_NOT_TYPING */
                  (GaimTypingState)typing);
}

static unsigned int mockprpl_send_typing(GaimConnection *gc, const char *name,
                                         GaimTypingState typing) {
  gaim_debug_info("mockprpl", "%s %s\n", gc->account->username,
                  typing_state_to_string(typing));
  foreach_mockprpl_gc(notify_typing, gc, (gpointer)typing);
  return 0;
}

static void mockprpl_get_info(GaimConnection *gc, const char *username) {
  gaim_debug_info("mockprpl", "Fetching %s's user info for %s\n",
                  username, gc->account->username);

  if (!get_mockprpl_gc(username)) {
    char *msg = g_strdup_printf(_("%s is not logged in."), username);
    gaim_notify_error(gc, _("User Info"), _("User info not available. "), msg);
    g_free(msg);
  }

  const char *info;
  GaimAccount *acct = gaim_accounts_find(username, MOCKPRPL_ID);
  if (acct)
    info = gaim_account_get_user_info(acct);
  if (!info)
    info = _("No user info.");

  /* show a buddy's user info in a nice dialog box */
  gaim_notify_userinfo(gc,        /* connection the buddy info came through */
                       username,  /* buddy's username */
                       info,      /* body */
                       NULL,      /* callback called when dialog closed */
                       NULL);     /* userdata for callback */
}

static void mockprpl_set_status(GaimAccount *acct, GaimStatus *status) {
  const char *msg = gaim_status_get_attr_string(status, "message");
  gaim_debug_info("mockprpl", "setting %s's status to %s: %s\n", acct->username,
                  gaim_status_get_name(status), msg);

  foreach_mockprpl_gc(report_status_change, get_mockprpl_gc(acct->username),
                      NULL);
}

static void mockprpl_set_idle(GaimConnection *gc, int idletime) {
  gaim_debug_info("mockprpl",
                  "gaim reports that %s has been idle for %d seconds\n",
                  gc->account->username, idletime);
}

static void mockprpl_change_passwd(GaimConnection *gc, const char *old_pass,
                                   const char *new_pass) {
  gaim_debug_info("mockprpl", "%s wants to change their password\n",
                  gc->account->username);
}

static void mockprpl_add_buddy(GaimConnection *gc, GaimBuddy *buddy,
                               GaimGroup *group)
{
  char *username = gc->account->username;
  gaim_debug_info("mockprpl", "adding %s to %s's buddy list\n",
                  buddy->name, username);

  GaimConnection *buddy_gc = get_mockprpl_gc(buddy->name);
  if (buddy_gc) {
    discover_status(gc, buddy_gc, NULL);

    GaimAccount *buddy_acct = buddy_gc->account;
    if (gaim_find_buddy(buddy_acct, username)) {
      gaim_debug_info("mockprpl", "%s is already on %s's buddy list\n",
                      username, buddy->name);
    } else {
      gaim_debug_info("mockprpl", "asking %s if they want to add %s\n",
                      buddy->name, username);
      gaim_account_request_add(buddy_acct,
                               username,
                               NULL,   /* local account id (rarely used) */
                               NULL,   /* alias */
                               NULL);  /* message */
    }
  }
}

static void mockprpl_add_buddies(GaimConnection *gc, GList *buddies,
                                 GList *groups) {
  gaim_debug_info("mockprpl", "adding multiple buddies\n");

  GList *buddy = buddies;
  GList *group = groups;

  while (buddy && group) {
    mockprpl_add_buddy(gc, (GaimBuddy *)buddy->data, (GaimGroup *)group->data);
    buddy = g_list_next(buddy);
    group = g_list_next(group);
  }
}

static void mockprpl_remove_buddy(GaimConnection *gc, GaimBuddy *buddy,
                                  GaimGroup *group)
{
  gaim_debug_info("mockprpl", "removing %s from %s's buddy list\n",
                  buddy->name, gc->account->username);
}

static void mockprpl_remove_buddies(GaimConnection *gc, GList *buddies,
                                    GList *groups) {
  gaim_debug_info("mockprpl", "removing multiple buddies\n");

  GList *buddy = buddies;
  GList *group = groups;

  while (buddy && group) {
    mockprpl_remove_buddy(gc, (GaimBuddy *)buddy->data,
                          (GaimGroup *)group->data);
    buddy = g_list_next(buddy);
    group = g_list_next(group);
  }
}

/*
 * mockprpl uses gaim's local whitelist and blacklist, stored in blist.xml, as
 * its authoritative privacy settings, and uses gaim's logic (specifically
 * gaim_privacy_check(), from privacy.h), to determine whether messages are
 * allowed or blocked.
 */
static void mockprpl_add_permit(GaimConnection *gc, const char *name) {
  gaim_debug_info("mockprpl", "%s adds %s to their allowed list\n",
                  gc->account->username, name);
}

static void mockprpl_add_deny(GaimConnection *gc, const char *name) {
  gaim_debug_info("mockprpl", "%s adds %s to their blocked list\n",
                  gc->account->username, name);
}

static void mockprpl_rem_permit(GaimConnection *gc, const char *name) {
  gaim_debug_info("mockprpl", "%s removes %s from their allowed list\n",
                  gc->account->username, name);
}

static void mockprpl_rem_deny(GaimConnection *gc, const char *name) {
  gaim_debug_info("mockprpl", "%s removes %s from their blocked list\n",
                  gc->account->username, name);
}

static void mockprpl_set_permit_deny(GaimConnection *gc) {
  /* this is for synchronizing the local black/whitelist with the server.
   * for mockprpl, it's a noop.
   */
}

static void joined_chat(GaimConvChat *from, GaimConvChat *to,
                        int id, const char *room, gpointer userdata) {
  /*  tell their chat window that we joined */
  gaim_debug_info("mockprpl", "%s sees that %s joined chat room %s\n",
                  to->nick, from->nick, room);
  gaim_conv_chat_add_user(to,
                          from->nick,
                          NULL,   /* user-provided join message, IRC style */
                          GAIM_CBFLAGS_NONE,
                          TRUE);  /* show a join message */

  if (from != to) {
    /* add them to our chat window */
    gaim_debug_info("mockprpl", "%s sees that %s is in chat room %s\n",
                    from->nick, to->nick, room);
    gaim_conv_chat_add_user(from,
                            to->nick,
                            NULL,   /* user-provided join message, IRC style */
                            GAIM_CBFLAGS_NONE,
                            FALSE);  /* show a join message */
  }
}

static void mockprpl_join_chat(GaimConnection *gc, GHashTable *components) {
  char *username = gc->account->username;
  char *room = g_hash_table_lookup(components, "room");
  int chat_id = g_str_hash(room);
  gaim_debug_info("mockprpl", "%s is joining chat room %s\n", username, room);

  if (!gaim_find_chat(gc, chat_id)) {
    serv_got_joined_chat(gc, chat_id, room);

    /* tell everyone that we joined, and add them if they're already there */
    foreach_gc_in_chat(joined_chat, gc, chat_id, NULL);
  } else {
    gaim_debug_info("mockprpl", "%s is already in chat room %s\n",
                    username, room);
    gaim_notify_info(gc,
                     _("Join chat"),
                     _("Join chat"),
                     g_strdup_printf("%s is already in chat room %s.",
                                     username, room));
  }
}

static void mockprpl_reject_chat(GaimConnection *gc, GHashTable *components) {
  char *invited_by = g_hash_table_lookup(components, "invited_by");
  char *room = g_hash_table_lookup(components, "room");
  char *username = gc->account->username;
  gaim_debug_info("mockprpl",
                  "%s has rejected %s's invitation to join chat room %s\n",
                  username, invited_by, room);

  GaimConnection *invited_by_gc = get_mockprpl_gc(invited_by);
  char *message = g_strdup_printf(
    "%s %s %s.",
    username,
    _("has rejected your invitation to join the chat room"),
    room);
  gaim_notify_info(invited_by_gc,
                   _("Chat invitation rejected"),
                   _("Chat invitation rejected"),
                   message);
}

static char *mockprpl_get_chat_name(GHashTable *components) {
  char *room = g_hash_table_lookup(components, "room");
  gaim_debug_info("mockprpl", "reporting chat room name '%s'\n", room);
  return room;
}

static void mockprpl_chat_invite(GaimConnection *gc, int id,
                                 const char *message, const char *who) {
  char *username = gc->account->username;
  GaimConversation *conv = gaim_find_chat(gc, id);
  char *room = conv->name;
  gaim_debug_info("mockprpl", "%s is inviting %s to join chat room %s\n",
                  username, who, room);

  GaimAccount *to_acct = gaim_accounts_find(who, MOCKPRPL_ID);
  if (to_acct) {
    GaimConversation *to_conv = gaim_find_chat(to_acct->gc, id);
    if (to_conv) {
      gaim_debug_info("mockprpl",
                      "%s is already in chat room %s; "
                      "ignoring invitation from %s\n",
                      who, room, username);
      gaim_notify_info(gc,
                       _("Chat invitation"),
                       _("Chat invitation"),
                       g_strdup_printf("%s is already in chat room %s.",
                                       who, room));
    } else {
      GHashTable *components;
      components = g_hash_table_new_full(g_str_hash, g_str_equal, NULL, free);
      g_hash_table_replace(components, "room", g_strdup(room));
      g_hash_table_replace(components, "invited_by", g_strdup(username));
      serv_got_chat_invite(to_acct->gc, room, username, message, components);
    }
  }
}

static void left_chat_room(GaimConvChat *from, GaimConvChat *to,
                           int id, const char *room, gpointer userdata) {
  if (from != to) {
    /*  tell their chat window that we left */
    gaim_debug_info("mockprpl", "%s sees that %s left chat room %s\n",
                    to->nick, from->nick, room);
    gaim_conv_chat_remove_user(to,
                               from->nick,
                               NULL);  /* user-provided message, IRC style */
  }
}

static void mockprpl_chat_leave(GaimConnection *gc, int id) {
  GaimConversation *conv = gaim_find_chat(gc, id);
  gaim_debug_info("mockprpl", "%s is leaving chat room %s\n",
                  gc->account->username, conv->name);

  /* tell everyone that we left */
  foreach_gc_in_chat(left_chat_room, gc, id, NULL);
}

static GaimCmdRet send_whisper(GaimConversation *conv, const gchar *cmd,
                               gchar **args, gchar **error, void *userdata) {
  /* parse args */
  assert(args[2] == NULL);
  const char *to_username = args[0];
  assert(to_username && strlen(to_username) > 0);
  const char *message = args[1];
  assert(message && strlen(message) > 0);

  const char *from_username = conv->account->username;
  gaim_debug_info("mockprpl", "%s whispers to %s in chat room %s: %s\n",
                  from_username, to_username, conv->name, message);

  GaimConvChat *chat = gaim_conversation_get_chat_data(conv);
  GaimConvChatBuddy* chat_buddy = gaim_conv_chat_cb_find(chat, to_username);
  GaimConnection *to = get_mockprpl_gc(to_username);

  if (!chat_buddy) {
    /* this will be freed by the caller */
    *error = g_strdup_printf(_("%s is not logged in."), to_username);
    return GAIM_CMD_RET_FAILED;
  } else if (!to) {
    *error = g_strdup_printf(_("%s is not in this chat room."), to_username);
    return GAIM_CMD_RET_FAILED;
  } else {
    /* write the whisper in the sender's chat window  */
    char *message_to = g_strdup_printf("%s (to %s)", message, to_username);
    gaim_conv_chat_write(chat, from_username, message_to,
                         GAIM_MESSAGE_SEND| GAIM_MESSAGE_WHISPER, time(NULL));
    g_free(message_to);

    /* send the whisper */
    serv_chat_whisper(to, chat->id, from_username, message);

    return GAIM_CMD_RET_OK;
  }
}

static void mockprpl_chat_whisper(GaimConnection *gc, int id, const char *who,
                                  const char *message) {
  char *username = gc->account->username;
  GaimConversation *conv = gaim_find_chat(gc, id);
  gaim_debug_info("mockprpl",
                  "%s receives whisper from %s in chat room %s: %s\n",
                  username, who, conv->name, message);

  /* receive whisper on recipient's account */
  serv_got_chat_in(gc, id, who, GAIM_MESSAGE_RECV | GAIM_MESSAGE_WHISPER,
                   message, time(NULL));
}

static void receive_chat_message(GaimConvChat *from, GaimConvChat *to,
                                 int id, const char *room, gpointer userdata) {
  const char *message = (const char *)userdata;
  GaimConnection *to_gc = get_mockprpl_gc(to->nick);

  gaim_debug_info("mockprpl",
                  "%s receives message from %s in chat room %s: %s\n",
                  to->nick, from->nick, room, message);
  serv_got_chat_in(to_gc, id, from->nick, GAIM_MESSAGE_RECV, message,
                   time(NULL));
}

static int mockprpl_chat_send(GaimConnection *gc, int id, const char *message,
                              GaimMessageFlags flags) {
  char *username = gc->account->username;
  GaimConversation *conv = gaim_find_chat(gc, id);

  if (conv) {
    gaim_debug_info("mockprpl", "%s is sending message to chat room %s: %s\n",
                    username, conv->name, message);

    /* send message to everyone in the chat room */
    foreach_gc_in_chat(receive_chat_message, gc, id, (gpointer)message);
    return 0;
  } else {
    gaim_debug_info("mockprpl",
                    "tried to send message from %s to chat room #%d: %s\n"
                    "but couldn't find chat room",
                    username, id, message);
    return -1;
  }
}

static void mockprpl_register_user(GaimAccount *acct) {
 gaim_debug_info("mockprpl", "registering account for %s\n",
                 acct->username);
}

static void mockprpl_get_cb_info(GaimConnection *gc, int id, const char *who) {
  GaimConversation *conv = gaim_find_chat(gc, id);
  gaim_debug_info("mockprpl", "retrieving %s's info for %s in chat room %s\n",
                  who, gc->account->username, conv->name);

  mockprpl_get_info(gc, who);
}

static void mockprpl_alias_buddy(GaimConnection *gc, const char *who,
                                 const char *alias) {
 gaim_debug_info("mockprpl", "%s sets %'s alias to %s\n",
                 gc->account->username, who, alias);
}

static void mockprpl_group_buddy(GaimConnection *gc, const char *who,
                                 const char *old_group,
                                 const char *new_group) {
  gaim_debug_info("mockprpl", "%s has moved %s from group %s to group %s\n",
                  who, old_group, new_group);
}

static void mockprpl_rename_group(GaimConnection *gc, const char *old_name,
                                  GaimGroup *group, GList *moved_buddies) {
  gaim_debug_info("mockprpl", "%s has renamed group %s to %s\n",
                  gc->account->username, old_name, group->name);
}

static void mockprpl_convo_closed(GaimConnection *gc, const char *who) {
  gaim_debug_info("mockprpl",
                  "%s's conversation with %s was closed\n",
                  gc->account->username, who);
}

/* normalize a username (e.g. remove whitespace, add default domain, etc.)
 * for mockprpl, this is a noop.
 */
static const char *mockprpl_normalize(const GaimAccount *acct,
                                      const char *input) {
  return NULL;
}

static void mockprpl_set_buddy_icon(GaimConnection *gc, const char *filename) {
 gaim_debug_info("mockprpl", "setting %s's buddy icon to %s\n",
                 gc->account->username, filename);
}

static void mockprpl_remove_group(GaimConnection *gc, GaimGroup *group) {
  gaim_debug_info("mockprpl", "%s has removed group %s\n",
                  gc->account->username, group->name);
}


static void set_chat_topic_fn(GaimConvChat *from, GaimConvChat *to,
                              int id, const char *room, gpointer userdata) {
  const char *topic = (const char *)userdata;
  const char *username = from->conv->account->username;

  gaim_conv_chat_set_topic(to, username, topic);

  char *msg;
  if (topic && strlen(topic) > 0)
    msg = g_strdup_printf(_("%s sets topic to: %s"), username, topic);
  else
    msg = g_strdup_printf(_("%s clears topic"), username);

  gaim_conv_chat_write(to, username, msg,
                       GAIM_MESSAGE_SYSTEM | GAIM_MESSAGE_NO_LOG, time(NULL));
  g_free(msg);
}

static void mockprpl_set_chat_topic(GaimConnection *gc, int id,
                                    const char *topic) {
  GaimConversation *conv = gaim_find_chat(gc, id);
  GaimConvChat *chat = gaim_conversation_get_chat_data(conv);
  if (!chat)
    return;

  gaim_debug_info("mockprpl", "%s sets topic of chat room '%s' to '%s'\n",
                  gc->account->username, conv->name, topic);

  const char *last_topic = gaim_conv_chat_get_topic(chat);
  if ((!topic && !last_topic) ||
      (topic && last_topic && !strcmp(topic, last_topic)))
    return;  /* topic is unchanged, this is a noop */

  foreach_gc_in_chat(set_chat_topic_fn, gc, id, (gpointer)topic);
}

static gboolean mockprpl_finish_get_roomlist(gpointer roomlist) {
  gaim_roomlist_set_in_progress((GaimRoomlist *)roomlist, FALSE);
  return FALSE;
}

static GaimRoomlist *mockprpl_roomlist_get_list(GaimConnection *gc) {
  char *username = gc->account->username;
  gaim_debug_info("mockprpl", "%s asks for room list; returning:\n", username);

  /* set up the room list */
  GaimRoomlist *roomlist = gaim_roomlist_new(gc->account);
  GList *fields =  NULL;
  GaimRoomlistField *field;

  field = gaim_roomlist_field_new(GAIM_ROOMLIST_FIELD_STRING, "room", "room",
                                  TRUE /* hidden */);
  fields = g_list_append(fields, field);

  field = gaim_roomlist_field_new(GAIM_ROOMLIST_FIELD_INT, "Id", "Id", FALSE);
  fields = g_list_append(fields, field);

  gaim_roomlist_set_fields(roomlist, fields);

  /* add each chat room. the chat ids are cached in seen_ids so that each room
   * is only returned once, even if multiple users are in it. */
  GList *chats;
  GList *seen_ids = NULL;

  for (chats  = gaim_get_chats(); chats; chats = g_list_next(chats)) {
    GaimConversation *conv = (GaimConversation *)chats->data;
    char *name = conv->name;
    int id = gaim_conversation_get_chat_data(conv)->id;

    /* have we already added this room? */
    if (g_list_find_custom(seen_ids, name, (GCompareFunc)strcmp))
      continue;                                /* yes! try the next one. */

    seen_ids = g_list_append(seen_ids, name);  /* no, it's new. */
    gaim_debug_info("mockprpl", "%s (%d), ", name, id);

    GaimRoomlistRoom *room = gaim_roomlist_room_new(
      GAIM_ROOMLIST_ROOMTYPE_ROOM, name, NULL);
    gaim_roomlist_room_add_field(roomlist, room, name);
    gaim_roomlist_room_add_field(roomlist, room, &id);
    gaim_roomlist_room_add(roomlist, room);
  }

  gaim_timeout_add(1 /* ms */, mockprpl_finish_get_roomlist, roomlist);
  return roomlist;
}

static void mockprpl_roomlist_cancel(GaimRoomlist *list) {
 gaim_debug_info("mockprpl", "%s asked to cancel room list request\n",
                 list->account->username);
}

static void mockprpl_roomlist_expand_category(GaimRoomlist *list,
                                              GaimRoomlistRoom *category) {
 gaim_debug_info("mockprpl", "%s asked to expand room list category %s\n",
                 list->account->username, category->name);
}

/* mockprpl doesn't support file transfer...yet... */
static gboolean mockprpl_can_receive_file(GaimConnection *gc,
                                          const char *who) {
  return FALSE;
}

static gboolean mockprpl_offline_message(const GaimBuddy *buddy) {
  gaim_debug_info("mockprpl",
                  "reporting that offline messages are supported for %s\n",
                  buddy->name);
  return TRUE;
}


/*
 * prpl stuff. see prpl.h for more information.
 */

static GaimPluginProtocolInfo prpl_info =
{
  .options                   = OPT_PROTO_NO_PASSWORD | OPT_PROTO_CHAT_TOPIC,
  .user_splits               = NULL,       /* initialized in mockprpl_init() */
  .protocol_options          = NULL,       /* initialized in mockprpl_init() */
  .icon_spec                 = {
      /* this is a GaimBuddyIconSpec */
      .format       = "png,jpg,gif",           /* supported image formats */
      .min_width    = 0,
      .min_height   = 0,
      .max_width    = 128,
      .max_height   = 128,
      .scale_rules  = GAIM_ICON_SCALE_DISPLAY, /* how to stretch buddy icons */
    },
  .list_icon                 = mockprpl_list_icon,
  .list_emblems              = mockprpl_list_emblems,
  .status_text               = mockprpl_status_text,
  .tooltip_text              = mockprpl_tooltip_text,
  .status_types              = mockprpl_status_types,
  .blist_node_menu           = mockprpl_blist_node_menu,
  .chat_info                 = mockprpl_chat_info,
  .chat_info_defaults        = mockprpl_chat_info_defaults,
  .login                     = mockprpl_login,
  .close                     = mockprpl_close,
  .send_im                   = mockprpl_send_im,
  .set_info                  = mockprpl_set_info,
  .send_typing               = mockprpl_send_typing,
  .get_info                  = mockprpl_get_info,
  .set_status                = mockprpl_set_status,
  .set_idle                  = mockprpl_set_idle,
  .change_passwd             = mockprpl_change_passwd,
  .add_buddy                 = mockprpl_add_buddy,
  .add_buddies               = mockprpl_add_buddies,
  .remove_buddy              = mockprpl_remove_buddy,
  .remove_buddies            = mockprpl_remove_buddies,
  .add_permit                = mockprpl_add_permit,
  .add_deny                  = mockprpl_add_deny,
  .rem_permit                = mockprpl_rem_permit,
  .rem_deny                  = mockprpl_rem_deny,
  .set_permit_deny           = mockprpl_set_permit_deny,
  .join_chat                 = mockprpl_join_chat,
  .reject_chat               = mockprpl_reject_chat,
  .get_chat_name             = mockprpl_get_chat_name,
  .chat_invite               = mockprpl_chat_invite,
  .chat_leave                = mockprpl_chat_leave,
  .chat_whisper              = mockprpl_chat_whisper,
  .chat_send                 = mockprpl_chat_send,
  .keepalive                 = NULL,
  .register_user             = mockprpl_register_user,
  .get_cb_info               = mockprpl_get_cb_info,
  .get_cb_away               = NULL,
  .alias_buddy               = mockprpl_alias_buddy,
  .group_buddy               = mockprpl_group_buddy,
  .rename_group              = mockprpl_rename_group,
  .buddy_free                = NULL,
  .convo_closed              = mockprpl_convo_closed,
  .normalize                 = mockprpl_normalize,
  .set_buddy_icon            = mockprpl_set_buddy_icon,
  .remove_group              = mockprpl_remove_group,
  .get_cb_real_name          = NULL,
  .set_chat_topic            = mockprpl_set_chat_topic,
  .find_blist_chat           = NULL,
  .roomlist_get_list         = mockprpl_roomlist_get_list,
  .roomlist_cancel           = mockprpl_roomlist_cancel,
  .roomlist_expand_category  = mockprpl_roomlist_expand_category,
  .can_receive_file          = mockprpl_can_receive_file,
  .send_file                 = NULL,
  .new_xfer                  = NULL,
  .offline_message           = mockprpl_offline_message,
  .whiteboard_prpl_ops       = NULL,
  .send_raw                  = NULL,
};

static void mockprpl_init(GaimPlugin *plugin)
{
  gaim_debug_info("mockprpl", "starting up\n");

  /* see accountopt.h for information about user splits and protocol options */
  GaimAccountUserSplit *split = gaim_account_user_split_new(
    _("Example user split (unused)"),  /* text shown to user */
    "default",                         /* default value */
    '@');                              /* field separator */
  prpl_info.user_splits = g_list_append(NULL, split);

  GaimAccountOption *option = gaim_account_option_string_new(
    _("Example option (unused)"),      /* text shown to user */
    "example",                         /* pref name */
    "default");                        /* default value */
  prpl_info.protocol_options = g_list_append(NULL, option);

  /* register whisper chat command, /msg */
  gaim_cmd_register("msg",
                    "ws",                /* args: recipient and message */
                    GAIM_CMD_P_DEFAULT,  /* priority */
                    GAIM_CMD_FLAG_CHAT,
                    "prpl-mock",
                    send_whisper,
                    "msg &lt;username&gt; &lt;message&gt;: send a private message, aka a whisper",
                    NULL);               /* userdata */

  /* get ready to store offline messages */
  goffline_messages = g_hash_table_new_full(g_str_hash,  /* hash fn */
                                            g_str_equal, /* key comparison fn */
                                            g_free,      /* key free fn */
                                            NULL);       /* value free fn */

  _mock_protocol = plugin;
}

static void mockprpl_destroy(GaimPlugin *plugin) {
  gaim_debug_info("mockprpl", "shutting down\n");
}


static GaimPluginInfo info =
{
  .magic           = GAIM_PLUGIN_MAGIC,
  .major_version   = GAIM_MAJOR_VERSION,
  .minor_version   = GAIM_MINOR_VERSION,
  .type            = GAIM_PLUGIN_PROTOCOL,
  .ui_requirement  = NULL,
  .flags           = 0,
  .dependencies    = NULL,
  .priority        = GAIM_PRIORITY_DEFAULT,
  .id              = MOCKPRPL_ID,
  .name            = "MockPrpl",
  .version         = "0.3",
  .summary         = "Mock Protocol Plugin",
  .description     = "Mock Protocol Plugin",
  .author          = "Ryan Barrett <mockprpl@ryanb.org>",
  .homepage        = "http://snarfed.org/space/gaim+mock+protocol+plugin",
  .load            = NULL,
  .unload          = NULL,
  .destroy         = mockprpl_destroy,
  .ui_info         = NULL,
  .extra_info      = &prpl_info,
  .prefs_info      = NULL,
  .actions         = mockprpl_actions,
};

GAIM_INIT_PLUGIN(mock, mockprpl_init, info);
