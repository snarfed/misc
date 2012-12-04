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
  GtkWidget *window, *menubar, *menu, *menuitem;
  GtkAccelGroup *accel_group;

  gtk_init(&argc, &argv);
  window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
 
  /* make a menu bar */
  menubar = gtk_menu_bar_new();
  gtk_container_add(GTK_CONTAINER(window), menubar);

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

  /****** THIS DOES IT!!! ******/
  accel_group = gtk_accel_group_new();
  gtk_menu_set_accel_group(GTK_MENU(menu), accel_group);
  gtk_menu_item_set_accel_path(GTK_MENU_ITEM(menuitem), "<main>/Foo");

  /* go go go! */
  gtk_widget_show_all(window);
  gtk_main();
 
  return 0;
}
