SOURCES=minimal.c #gtktest.c #manual.c 
GTK_FLAGS=`pkg-config --cflags --libs gtk+-2.0`
GLIB_FLAGS=`pkg-config --libs glib-2.0`

all:
	echo $(GTK_FLAGS) $(GLIB_FLAGS)
	gcc -Wall -g $(SOURCES) -o gtktest $(GTK_FLAGS) $(GLIB_FLAGS)
