/*
 * gaim gtk test program. (tests why i can't add kbd shortcuts to manually
 * created menus.)
 *
 * - manually created items on itemfactory menus work
 *
 * Ryan Barrett
 * http://ryan.barrett.name/
 */

#include <stdio.h>
#include <gtk/gtk.h>


static GtkItemFactoryEntry menu_items[] =
{
  { "/_Foo", NULL, NULL, 0, "<Branch>" },
  { "/Foo/Baj", NULL, NULL, 0, "<Item>" },

  /* these are created manually in main()...
   * { "/_Bar", NULL, NULL, 0, "<Branch>" },
   * { "/Bar/Baffle", NULL, NULL, 0, "<Item>" },
   */
};

int main(int argc, char *argv[])
{
  GtkWidget *window, *vbox, *menubar, *menu, *menuitem;
  GtkItemFactory *item_factory;

  gtk_init(&argc, &argv);
  window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
 
  /* Make a vbox to put the menu in */
  vbox = gtk_vbox_new (FALSE, 1);
  gtk_container_add(GTK_CONTAINER (window), vbox);

  /* Make an ItemFactory (that makes a menubar) */
  item_factory = gtk_item_factory_new(GTK_TYPE_MENU_BAR, "<main>", NULL);
  gtk_item_factory_create_items(item_factory, 2, menu_items, NULL);
  menubar = gtk_item_factory_get_widget(item_factory, "<main>");

  /* add the /Bar menu */
  menuitem = gtk_menu_item_new_with_mnemonic("_Bar");
  gtk_menu_shell_append(GTK_MENU_SHELL(menubar), menuitem);
  gtk_widget_show(menuitem);
  menu = gtk_menu_new();
  gtk_menu_item_set_submenu(GTK_MENU_ITEM(menuitem), menu);

  /* add the /Bar/Baffle menu item */
  menuitem = gtk_menu_item_new_with_label("Baffle");
  gtk_menu_shell_append(GTK_MENU_SHELL(menu), menuitem);
  gtk_widget_show(menuitem);

  /* Pack it all together */
  gtk_box_pack_start(GTK_BOX (vbox), menubar, FALSE, TRUE, 0);
  gtk_widget_show_all(window);
  gtk_main();
 
  return 0;
}
