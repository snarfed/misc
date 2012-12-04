/*
 * gaim gtk test program. (tests why i can't add kbd shortcuts to third-level
 * submenus.)
 */

#include <stdio.h>
#include <gtk/gtk.h>


static gint button_press (GtkWidget *, GdkEvent *);
static void menuitem_response (gchar *);

int main( int   argc,
          char *argv[] )
{

    GtkWidget *window;
    GtkWidget *menu, *submenu;
    GtkWidget *menu_bar;
    GtkWidget *root_menu;
    GtkWidget *menuitem;
    GtkWidget *vbox;
    GtkWidget *button;
    GtkAccelGroup *accel_group;
    char buf[128];
    int i;

    gtk_init (&argc, &argv);

    /* create a new window */
    window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
    gtk_widget_set_size_request (GTK_WIDGET (window), 200, 100);
    gtk_window_set_title (GTK_WINDOW (window), "GTK Menu Test");
    g_signal_connect (G_OBJECT (window), "delete_event",
                      G_CALLBACK (gtk_main_quit), NULL);

    /* Make an accelerator group (shortcut keys) */
    accel_group = gtk_accel_group_new();
	gtk_window_add_accel_group(GTK_WINDOW (window), accel_group);

    /* Init the menu-widget, and remember -- never
     * gtk_show_widget() the menu widget!! 
     * This is the menu that holds the menu items, the one that
     * will pop up when you click on the "Root Menu" in the app */
    menu = gtk_menu_new();
	gtk_menu_set_accel_group(GTK_MENU_SHELL(menu), accel_group);

	// top-level menu item
	menuitem = gtk_menu_item_new_with_label("Bar");
	gtk_menu_shell_append(GTK_MENU_SHELL(menu), menuitem);
	gtk_widget_show(menuitem);

	// second level menu
	submenu = gtk_menu_new();
	gtk_menu_item_set_submenu(GTK_MENU_ITEM(menuitem), submenu);
	gtk_widget_show(submenu);

	// second level item
	menuitem = gtk_menu_item_new_with_label("Fah");
	gtk_menu_shell_append(GTK_MENU_SHELL(submenu), menuitem); // ???
	gtk_widget_show(menuitem);

	// second level item
	menuitem = gtk_menu_item_new_with_label("Gah");
	gtk_menu_shell_append(GTK_MENU_SHELL(submenu), menuitem); // ???
	gtk_widget_show(menuitem);

	// second level menu
	submenu = gtk_menu_new();
	gtk_menu_item_set_submenu(GTK_MENU_ITEM(menuitem), submenu);
	gtk_widget_show(submenu);

	// third level item
	menuitem = gtk_menu_item_new_with_label("Baz");
	gtk_menu_shell_append(GTK_MENU_SHELL(submenu), menuitem); // ???
	gtk_widget_show(menuitem);



    /* This is the root menu, and will be the label
     * displayed on the menu bar.  There won't be a signal handler attached,
     * as it only pops up the rest of the menu when pressed. */
    root_menu = gtk_menu_item_new_with_label ("Root Menu");

    gtk_widget_show (root_menu);

    /* Now we specify that we want our newly created "menu" to be the menu
     * for the "root menu" */
    gtk_menu_item_set_submenu (GTK_MENU_ITEM (root_menu), menu);

    /* A vbox to put a menu and a button in: */
    vbox = gtk_vbox_new (FALSE, 0);
    gtk_container_add (GTK_CONTAINER (window), vbox);
    gtk_widget_show (vbox);

    /* Create a menu-bar to hold the menus and add it to our main window */
    menu_bar = gtk_menu_bar_new ();
    gtk_box_pack_start (GTK_BOX (vbox), menu_bar, FALSE, FALSE, 2);
    gtk_widget_show (menu_bar);

    /* Create a button to which to attach menu as a popup */
    button = gtk_button_new_with_label ("press me");
    g_signal_connect_swapped (G_OBJECT (button), "event",
	                      G_CALLBACK (button_press), 
                              G_OBJECT (menu));
    gtk_box_pack_end (GTK_BOX (vbox), button, TRUE, TRUE, 2);
    gtk_widget_show (button);

    /* And finally we append the menu-item to the menu-bar -- this is the
     * "root" menu-item I have been raving about =) */
    gtk_menu_shell_append (GTK_MENU_SHELL (menu_bar), root_menu);

    /* always display the window as the last step so it all splashes on
     * the screen at once. */
    gtk_widget_show (window);

    gtk_main ();

    return 0;
}

/* Respond to a button-press by posting a menu passed in as widget.
 *
 * Note that the "widget" argument is the menu being posted, NOT
 * the button that was pressed.
 */

static gint button_press( GtkWidget *widget,
                          GdkEvent *event )
{

    if (event->type == GDK_BUTTON_PRESS) {
        GdkEventButton *bevent = (GdkEventButton *) event; 
        gtk_menu_popup (GTK_MENU (widget), NULL, NULL, NULL, NULL,
                        bevent->button, bevent->time);
        /* Tell calling code that we have handled this event; the buck
         * stops here. */
        return TRUE;
    }

    /* Tell calling code that we have not handled this event; pass it on. */
    return FALSE;
}


/* Print a string when a menu item is selected */

static void menuitem_response( gchar *string )
{
    printf ("%s\n", string);
}
