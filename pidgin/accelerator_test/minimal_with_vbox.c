/*
 * gaim gtk test program. (tests why i can't add kbd shortcuts to manually
 * created menus.)
 *
 * Ryan Barrett
 * http://ryan.barrett.name/
 */

#include <gtk/gtk.h>


int main(int argc, char *argv[])
{
  GtkWidget *window, *vbox, *menubar, *menu, *menuitem;

  gtk_init(&argc, &argv);
  window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
 
  /* make a vbox to put the menu in */
  vbox = gtk_vbox_new (FALSE, 1);
  gtk_container_add(GTK_CONTAINER(window), vbox);

  /* make a menu bar */
  menubar = gtk_menu_bar_new();

  /* add the /Foo top-level menu */
  menuitem = gtk_menu_item_new_with_mnemonic("_Foo");
  gtk_menu_shell_append(GTK_MENU_SHELL(menubar), menuitem);
  gtk_widget_show(menuitem);

  menu = gtk_menu_new();
  gtk_menu_item_set_submenu(GTK_MENU_ITEM(menuitem), menu);

  /* add the /Foo/Bar menu item */
  menuitem = gtk_menu_item_new_with_mnemonic("_Bar");
  gtk_menu_shell_append(GTK_MENU_SHELL(menu), menuitem);
  gtk_widget_show(menuitem);

  /* go go go! */
  gtk_box_pack_start(GTK_BOX(vbox), menubar, FALSE, TRUE, 0);
  gtk_widget_show_all(window);
  gtk_box_pack_end(GTK_BOX(vbox), menubar, FALSE, TRUE, 0);
  gtk_main();
 
  return 0;
}
