/*
 * gaim gtk test program. (tests why i can't add kbd shortcuts to third-level
 * submenus.)
 *
 * Ryan Barrett
 * http://ryan.barrett.name/
 */

#include <stdio.h>
#include <gtk/gtk.h>


static GtkItemFactoryEntry menu_items[] =
{
  { "/_Foo", NULL, NULL, 0, "<Branch>" },
  { "/Foo/Bar", NULL, NULL, 0, "<Branch>" },
  { "/Foo/Bar/Baz", NULL, NULL, 0, "<Item>" },
  /* these are created manually...
   * { "/Foo/Baj", NULL, NULL, 0, "<Branch>" },
   * { "/Foo/Baj/Baffle!", NULL, NULL, 0, "<Item>" },
   */
};

int main(int argc, char *argv[])
{
  GtkWidget *window, *vbox, *menubar, *menu, *menuitem;
  GtkItemFactory *item_factory;
  GtkAccelGroup *accel_group;

  gtk_init(&argc, &argv);
  window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
 
  /* Make a vbox to put the menu in */
  vbox = gtk_vbox_new (FALSE, 1);
  gtk_container_add(GTK_CONTAINER (window), vbox);

  /* Make an accel group */
  accel_group = gtk_accel_group_new();
  gtk_window_add_accel_group(GTK_WINDOW(window), accel_group);
  g_object_unref(accel_group);

  /* Make an ItemFactory (that makes a menubar) */
  item_factory = gtk_item_factory_new(GTK_TYPE_MENU_BAR, "<main>", accel_group);
  gtk_item_factory_create_items(item_factory, 3, menu_items, NULL);
  menubar = gtk_item_factory_get_widget(item_factory, "<main>");

  /* get the /Foo submenu */
  menu = gtk_item_factory_get_widget(item_factory, "/Foo");

  /* add the /Foo/Baj submenu */
  menuitem = gtk_menu_item_new_with_label("Baj");
  gtk_menu_shell_append(GTK_MENU_SHELL(menu), menuitem);
  gtk_widget_show(menuitem);

  menu = gtk_menu_new();
  gtk_menu_item_set_submenu(GTK_MENU_ITEM(menuitem), menu);
  gtk_menu_set_accel_group(GTK_MENU(menu), accel_group);
  gtk_widget_show(menu);

  /* add the /Foo/Baj/Baffle menu item */
  menuitem = gtk_menu_item_new_with_label("Baffle");
  gtk_menu_shell_append(GTK_MENU_SHELL(menu), menuitem);
  gtk_widget_show(menuitem);

  /* Pack it all together */
  gtk_box_pack_start(GTK_BOX (vbox), menubar, FALSE, TRUE, 0);
  gtk_widget_show_all(window);
  gtk_main();
 
  return 0;
}
