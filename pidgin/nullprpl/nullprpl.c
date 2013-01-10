/**
 * gaim - Null Protocol Plugin
 * http://snarfed.org/space/gaim+null+protocol+plugin
 * Copyright (C) 2004, Ryan Barrett <nullprpl@ryanb.org>
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

#include "account.h"
#include "debug.h"
#include "internal.h"
#include "notify.h"
#include "prpl.h"
#include "version.h"

#include <stdarg.h>
#include <glib.h>

#define NULLPRPL_ID "prpl-null"
static GaimPlugin *my_protocol = NULL;

foo(barbarbar,
	(x, y),
	baz);

/*
 * utility functions
 */

typedef void (*AccountFunc)(GaimAccount *notifier, GaimAccount *notifiee,
							gpointer userdata);

typedef struct {
	AccountFunc fn;
	GaimAccount *notifier;
	gpointer userdata;
} AccountFuncData;

static void call_if_connected_nullprpl(gpointer data, gpointer userdata) {
	GaimAccount *acct = (GaimAccount *)(data);
	AccountFuncData *afdata = (AccountFuncData *)userdata;

	if (!strcmp(acct->protocol_id, NULLPRPL_ID) &&
		gaim_account_is_connected(acct))
		afdata->fn(afdata->notifier, acct, afdata->userdata);
}

static void foreach_connected_nullprpl_account(AccountFunc fn,
											   GaimAccount *notifier,
											   gpointer userdata) {
	AccountFuncData afdata = { fn, notifier, userdata };
	g_list_foreach(gaim_accounts_get_all(), call_if_connected_nullprpl,
				   (gpointer)&afdata);
}

static GaimAccount *get_connected_nullprpl_account(const char *username) {
	GaimAccount *acct = gaim_accounts_find(username, NULLPRPL_ID);
	if (acct && gaim_account_is_connected(acct))
		return acct;
	else
		return NULL;
}


/*
 * prpl functions
 */
static const char *nullprpl_list_icon(GaimAccount *acct, GaimBuddy *buddy)
{
	return "nullprpl";
}

/*
 * logged_in is the GaimAccount* of the account that logged in or out.
 */
void notify_connection_change(GaimAccount *notifier, GaimAccount *notifiee,
							  gpointer userdata) {
	if (gaim_find_buddy(notifiee, notifier->username)) {
		gaim_debug_info("nullprpl", "(%acct) notified that %s logged in\n",
						notifiee->username, notifier->username);
		serv_got_update(gaim_account_get_connection(notifiee),
						notifier->username,
						gaim_account_is_connected(notifier),
						0 /* warning level */,
						0 /* signon time */,
						0 /* idle time */,
						0 /* type */);
	}
}

static void nullprpl_login(GaimAccount *acct)
{
	/* handle login */
	GaimConnection *gc = gaim_account_get_connection(acct);
	gaim_debug_info("nullprpl", "(%s) logging in\n", gc->account->username);
	gaim_connection_set_state(gc, GAIM_CONNECTED);
	serv_finish_login(gc);

	/* notify other nullprpl accounts */
	foreach_connected_nullprpl_account(notify_connection_change, acct, NULL);
}

static void nullprpl_logoff(GaimConnection *gc)
{
	/* notify other nullprpl accounts */
	foreach_connected_nullprpl_account(notify_connection_change, gc->account,
									   NULL);
}

static void nullprpl_add_buddy(GaimConnection *gc, GaimBuddy *buddy,
							   GaimGroup *group)
{
	gaim_debug_info("nullprpl", "(%s) adding buddy %s\n",
					gc->account->username, buddy->name);

	GaimAccount *buddy_acct = get_connected_nullprpl_account(buddy->name);
	if (buddy_acct) {
		notify_connection_change(buddy_acct, gc->account, NULL);
		/* this should be gaim_account_request_add, but for some reason, the
		 * meat of it is commented out in gaim 1.5.0. also, the order of the
		 * first two arguments switched between 1.5 and 2.0. wtf?!?
		 */
/* 		gaim_account_notify_added(buddy_acct, */
/* 								  gc->account->username /\* username *\/, */
/* 								  gc->account->username /\* local acct id *\/, */
/* 								  NULL /\* alias *\/, NULL /\* message *\/); */
	}
}

static void nullprpl_remove_buddy(GaimConnection *gc, GaimBuddy *buddy,
								  GaimGroup *group)
{
	gaim_debug_info("nullprpl", "(%s) removing buddy: %s\n",
					gc->account->username, buddy->name);
}

static int nullprpl_send_im(GaimConnection *gc, const char *who,
							const char *message, GaimConvImFlags flags)
{
	gaim_debug_info("nullprpl", "(%s) sending im to %s: %s\n",
					gc->account->username, who, message);

	/* is the recipient online? */
	GaimAccount *recip = get_connected_nullprpl_account(who);
	if (recip) {  /* yes, send */
		GaimConnection *conn = gaim_account_get_connection(recip);
		serv_got_im(conn, gc->account->username, message, flags, time(NULL));
		gaim_debug_info("nullprpl", "(%s) received im: %s", who, message);
		return 1;

	} else {  /* nope, complain */
		return 0;
	}
}

static void nullprpl_set_info(GaimConnection *gc, const char *info) {
	gaim_account_set_user_info(gc->account, info);
}

void notify_typing(GaimAccount *notifier, GaimAccount *notifiee,
				   gpointer typing) {
	serv_got_typing(gaim_account_get_connection(notifiee),
					notifier->username,
					0 /* if non-zero, a timeout in seconds after which to
					   * reset the typing status to GAIM_NOT_TYPING
					   */,
					(GaimTypingState)typing);
}

int nullprpl_send_typing(GaimConnection *gc, const char *name, int typing) {
	gaim_debug_info("nullprpl", "(%s) started typing\n", gc->account->username);
	foreach_connected_nullprpl_account(notify_typing, gc->account,
									   (gpointer)typing);
	return 0;
}

static void nullprpl_get_info(GaimConnection *gc, const char *username) {
	const char *info = "No user info.";
	GaimAccount *acct = gaim_accounts_find(username, NULLPRPL_ID);
    if (acct)
		info = gaim_account_get_user_info(acct);

	/* show a buddy's user info in a nice dialog box */
	gaim_notify_userinfo(gc,  /* connection the buddy info came through */
						 username,  /* buddy's username */
						 username,  /* dialog box title */
						 _("Buddy Information"),  /* primary heading */
						 NULL,  /* secondary heading */
						 info,  /* body */
						 NULL,  /* callback called when dialog closed */
						 NULL   /* userdata for callback */);
}

static GList *nullprpl_away_states(GaimConnection *gc)
{
	GList *m = NULL;

	m = g_list_append(m, GAIM_AWAY_CUSTOM);
	m = g_list_append(m, _("Back"));

	return m;
}

static void nullprpl_set_away(GaimConnection *gc, const char *state,
                              const char *message) {
}

static void nullprpl_set_idle(GaimConnection *gc, int idletime) {
}

static void nullprpl_change_passwd(GaimConnection *gc, const char *old_pass,
                                   const char *new_pass) {
}

static void nullprpl_add_buddies(GaimConnection *gc, GList *buddies,
                                 GList *groups) {
}

static void nullprpl_remove_buddies(GaimConnection *gc, GList *buddies,
                                    GList *groups) {
}

static void nullprpl_add_permit(GaimConnection *gc, const char *name) {
}

static void nullprpl_add_deny(GaimConnection *gc, const char *name) {
}

static void nullprpl_rem_permit(GaimConnection *gc, const char *name) {
}

static void nullprpl_rem_deny(GaimConnection *gc, const char *name) {
}

static void nullprpl_set_permit_deny(GaimConnection *gc) {
}

static void nullprpl_warn(GaimConnection *gc, const char *who,
                          gboolean anonymous) {
}

static void nullprpl_join_chat(GaimConnection *gc, GHashTable *components) {
}

static void nullprpl_reject_chat(GaimConnection *gc, GHashTable *components) {
}

static char *nullprpl_get_chat_name(GHashTable *components) {
}

static void nullprpl_chat_invite(GaimConnection *gc, int id, const char *who,
                                 const char *message) {
}

static void nullprpl_chat_leave(GaimConnection *gc, int id) {
}

static void nullprpl_chat_whisper(GaimConnection *gc, int id, const char *who,
                                  const char *message) {
}

static int  nullprpl_chat_send(GaimConnection *gc, int id, const char *message) {
}

static void nullprpl_keepalive(GaimConnection *gc) {
}

static void nullprpl_register_user(GaimAccount *acct) {
}

static void nullprpl_get_cb_info(GaimConnection *gc, int index,
								 const char *who) {
}

static void nullprpl_get_cb_away(GaimConnection *gc, int index,
								 const char *who) {
}

static void nullprpl_alias_buddy(GaimConnection *gc, const char *who,
                                 const char *alias) {
}

static void nullprpl_group_buddy(GaimConnection *gc,
                                 const char *who,
                                 const char *old_group,
                                 const char *new_group) {
}

static void nullprpl_rename_group(GaimConnection *gc, const char *old_name,
                                  GaimGroup *group, GList *moved_buddies) {
}

static void nullprpl_buddy_free(GaimBuddy *buddy) {
}

static void nullprpl_convo_closed(GaimConnection *gc, const char *who) {
}

static const char *nullprpl_normalize(const GaimAccount *acct,
									  const char *string) {
}

static void nullprpl_set_buddy_icon(GaimConnection *gc, const char *filename) {
}

static void nullprpl_remove_group(GaimConnection *gc, GaimGroup *group) {
}

static char *nullprpl_get_cb_real_name(GaimConnection *gc, int id,
                                       const char *who) {
}

static void nullprpl_set_chat_topic(GaimConnection *gc, int id,
                                    const char *topic) {
}

static GaimChat *nullprpl_find_blist_chat(GaimAccount *account,
                                          const char *name) {
}

static struct _GaimRoomlist *nullprpl_roomlist_get_list(GaimConnection *gc) {
}

static void nullprpl_roomlist_cancel(struct _GaimRoomlist *list) {
}

static void nullprpl_roomlist_expand_category(struct _GaimRoomlist *list,
                                     struct _GaimRoomlistRoom *category) {
}

static gboolean nullprpl_can_receive_file(GaimConnection *gc, const char *who) {
}

static void nullprpl_send_file(GaimConnection *gc, const char *who,
                               const char *filename) {
}



/* static void show_set_info(GaimPluginAction *action) */
/* { */
/* 	GaimConnection *gc = (GaimConnection *)action->context; */
/* 	gaim_account_request_change_user_info(gaim_connection_get_account(gc)); */
/* } */

/* static GList *nullprpl_actions(GaimPlugin *plugin, gpointer context) */
/* { */
/* 	GaimPluginAction *action = gaim_plugin_action_new(_("Set User Info"), */
/* 													  show_set_info); */
/* 	return g_list_append(NULL, action); */
/* } */



/*
 * prpl stuff
 */

static GaimPluginProtocolInfo prpl_info =
{
	OPT_PROTO_NO_PASSWORD,
	NULL,					/* user_splits */
	NULL,					/* protocol_options */
	NO_BUDDY_ICONS,			/* icon_spec */
	nullprpl_list_icon,		/* list_icon */
	NULL,					/* list_emblems */
	NULL,					/* status_text */
	NULL,					/* tooltip_text */
	nullprpl_away_states,	/* away_states */
	NULL,					/* blist_node_menu */
	NULL,					/* chat_info */
	NULL,					/* chat_info_defaults */
	nullprpl_login,			/* login */
	nullprpl_logoff,		/* close */
	nullprpl_send_im,		/* send_im */
	nullprpl_set_info,		/* set_info */
	nullprpl_send_typing,	/* send_typing */
	NULL,					/* get_info */
	nullprpl_set_away,		/* set_away */
	NULL,					/* set_idle */
	NULL,					/* change_passwd */
	nullprpl_add_buddy,		/* add_buddy */
	NULL,					/* add_buddies */
	nullprpl_remove_buddy,	/* remove_buddy */
	NULL,					/* remove_buddies */
	NULL,					/* add_permit */
	NULL,					/* add_deny */
	NULL,					/* rem_permit */
	NULL,					/* rem_deny */
	NULL,					/* set_permit_deny */
	NULL,					/* warn */
	NULL,					/* join_chat */
	NULL,					/* reject chat invite */
	NULL,					/* chat_invite */
	NULL,					/* chat_leave */
	NULL,					/* chat_whisper */
	NULL,					/* chat_send */
	NULL,					/* keepalive */
	NULL,					/* register_user */
	NULL,					/* get_cb_info */
	NULL,					/* get_cb_away */
	NULL,					/* alias_buddy */
	NULL,					/* group_buddy */
	NULL,					/* rename_group */
	NULL,					/* buddy_free */
	NULL,					/* convo_closed */
	NULL,					/* normalize */
	NULL,					/* set_buddy_icon */
	NULL,					/* remove_group */
	NULL,					/* get_cb_real_name */
	NULL,					/* set_chat_topic */
	NULL,					/* find_blist_chat */
	NULL,					/* roomlist_get_list */
	NULL,					/* roomlist_cancel */
	NULL,					/* roomlist_expand_category */
	NULL,					/* can_receive_file */
	NULL					/* send_file */
};


static GaimPluginInfo info =
{
	GAIM_PLUGIN_MAGIC,
	GAIM_MAJOR_VERSION,
	GAIM_MINOR_VERSION,
	GAIM_PLUGIN_PROTOCOL,                             /**< type           */
	NULL,                                             /**< ui_requirement */
	0,                                                /**< flags          */
	NULL,                                             /**< dependencies   */
	GAIM_PRIORITY_DEFAULT,                            /**< priority       */

	NULLPRPL_ID,                                      /**< id             */
	"NullPrpl",                                       /**< name           */
	"0.1",                                            /**< version        */
	                                                  /**  summary        */
	N_("Null Protocol Plugin"),
	                                                  /**  description    */
	N_("Null Protocol Plugin"),
	"Ryan Barrett <nullprpl@ryanb.org>",              /**< author         */
	"http://snarfed.org/space/gaim-nullprpl",         /**< homepage       */

	NULL,                                             /**< load           */
	NULL,                                             /**< unload         */
	NULL,                                             /**< destroy        */

	NULL,                                             /**< ui_info        */
	&prpl_info,                                       /**< extra_info     */
	NULL,
	NULL
};

static void
init_plugin(GaimPlugin *plugin)
{
	my_protocol = plugin;
}

GAIM_INIT_PLUGIN(null, init_plugin, info);
