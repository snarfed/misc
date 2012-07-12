package WWW::Netflix;

use strict;
use warnings;

use WWW::Mechanize;

our $VERSION = 0.05;

sub new {
    my $ref = shift;
    my $class = ref( $ref ) || $ref;

    my $self = bless {
        www => new WWW::Mechanize(),
    }, $class;

    return $self;
}

sub login {
    my ( $self, $user, $pass ) = @_;
    die "Netflix requires a username and password" 
        unless ( $user && $pass );

    $self->{ www }->get('http://www.netflix.com/Login');
    die "couldn't find login form" 
        unless ( $self->{ www }->content =~ /login-form/ ); 
    
    $self->{ www }->form_id( 'login-form' );
    $self->{ www }->set_fields(
        email     => $user,
        password  => $pass,
    );
    $self->{ www }->submit();
    die "login incorrect\n" 
        if ( $self->{ www }->content =~ /does not match an account/ );
    $self->{ www }->get("http://www.netflix.com");
    die ( "not logged in" )
        unless ( $self->{ www }->content =~ /Your Account/ );
}

sub getRatings {
    my ( $self ) = @_;

    my $movies;
    my $body = '';
    my $cur = 1;

    # loop through each page of ratings 
    while ( $body !~ /next-inactive/i ) {
        $self->{ www }->get( "http://www.netflix.com/MoviesYouveSeen?lnkctr=wizMovUC&pn=$cur" );

        # the page gets returned even if not logged in or 
        # if you don't have any ratings, 
        # but this text doesn't appear unless you are logged in
        # and you have ratings
        return 
            unless ( $self->{ www }->content =~ /this is the list of movies and TV shows you've seen/ );
        $body = $self->{ www }->content();
    
        # loop through and add each rating on the page
        #
        # example HTML:
        #  <div id="M60025026_496715_29_2" ...>
        #    <span ...>
        #    <div ...>
        #    [etc]
        #      You rated this movie: 5
        #
        # note the //m multi-line modifier on the regexp, that makes . match newline.
        # the <cr> tells it what constitutes a newline.
        #
        while ( $body =~ /<div id="M(\d+).*?You rated this movie: (\d)(\.\d)?/gs ) {
            my ( $movie_id, $rating ) = ( $1, $2 );
            $movies->{ $movie_id }->{ rating } = $rating;
        }

        # start over, loop through and add each movie title on the page
        #
        # example HTML:
        # <a id="..." href="http://movies.netflix.com/Movie/Adaptation/60025026&trkid=135440" ...> Adaptation </a>
        while ( $body =~ /Movie\/([^\/]+)\/(\d+)\D/gs ) {
            $movies->{ $2 }->{ title } = $1;
        }
        ++$cur;
    } # end of looping through pages

    # return all of the ratings as a hashref
    return $self->{ rated_movies } = $movies;
}

sub getRating {
    my ( $self, $movie_id ) = @_;
    $self->getRatings unless ( exists $self->{ rated_movies } );
    return $self->{ rated_movies }{ $movie_id }{ rating };
}

sub getTitle {
    my ( $self, $movie_id ) = @_;
    $self->getRatings unless ( exists $self->{ rated_movies } );
    return $self->{ rated_movies }{ $movie_id }{ title };
}


sub setRating {
    my ( $self, $movie_id, $rating ) = @_;

    die 'movie id must be an integer' 
        unless ( $movie_id =~ /^\d+$/ );
    die 'rating must be an integer between 1 and 5' 
        unless ( $rating =~ /^[1-5]$/ ); 

    # my $uri = "http://www.netflix.com/SetRating?movieid=${movie_id}&value=${rating}&url=http%3A%2F%2Fwww.netflix.com%2FMovieDisplay%3Fmovieid%3D${movie_id}";
    my $uri = "http://www.netflix.com/SetRating?movieid=${movie_id}&value=${rating}";
    $self->{ www }->get( $uri );
    
    # keep our hash up to date with reality
    $self->{ rated_movies }{ $movie_id }{ rating } = $rating if ( defined $self->{ rated_movies } );
}


sub getQueue {
  my ( $self ) = @_;

    $self->{www}->get( 'http://www.netflix.com/Queue' );
    my $body = $self->{www}->content();

    # this relies on the current state of the HTML where 
    # each of the headers and movies is on its own line
	$self->{ queue }{ home } = [];
    $self->{ queue }{ queued } = [];
    $self->{ queue }{ saved }  = [];
    my $section = 'throwaway';
    for my $line ( split "\n", $body ) {
        chomp $line;
        if ( $line =~ m{<span class="dvd_hdr">DVDs</span> At Home} ) {
            $section = 'home';
        }
        elsif ( $line =~ m{<span class="dvd_hdr">DVD</span> Queue} ) {
            $section = 'queued';
        }
        elsif ( $line  =~ m{Saved <span class="dvd_hdr">DVDs} ) {
            $section = 'saved';
        }
        elsif ( $line =~ m{<a href="http://www.netflix.com/Movie/\w+/(\d+)[^>]+>([^<]+)<} ) {
            # $1 is movie ID; $2 is movie title
            push @{ $self->{ queue }{ $section } }, [ $1 => $2 ]
                unless ( $section eq 'throwaway' ); # throwaway = recently watched movies
       }
    }

    # er, returning a hashref that the using code could modify ... that's a no-no.
    return $self->{ queue };
}

sub queueMovie {
  my ( $self, $id ) = @_;

    die "Movie ID must be a series of one or more numerical digits.\n"
        unless $id =~ /^\d+$/;

    #http://www.netflix.com/AddToQueue?movieid=70027897&ftype=DD&trkid=199898
    
    my $url = "http://www.netflix.com/AddToQueue?movieid=$id";
    $self->{ www }->get( $url );

    return $self->{ www }->uri() =~ /QueueAddConfirmation/ ? 1 : 0;
}



1;

__END__
=pod

=head1 NAME

WWW::Netflix - Get and set ratings and queue for any Netflix account.
(This module used to be called Net::Netflix.)

=head1 DESCRIPTION

The included C<netlix_mover> script does the work of retrieving ratings and
queued movies from one account or saving them to another account. You will
probably just want to use it.

This module is designed to pull down every movie you've ever rated using
your Netflix account, or a list of the movies in your queue. It can also
be used to set the ratings or the queue on another account. It would be
a good idea to use this if you were looking to transfer your ratings or
your queue to another Netflix account.

Currently does not work for "Not Interested" ratings. It would also
be nice to have methods to clear ratings and to remove a movie from
the queue.

=head1 SYNOPSIS

    use WWW::Netflix;
    use Data::Dumper;

    # log into a Netflix account
    my $old_netflix = WWW::Netflix->new();
    $old_netflix->login( 'USERNAME', 'PASSWORD' );
    
    # get ratings from the old Netflix account and print them
    my $ratings = $old_netflix->getRatings();  
    print Dumper( $ratings );
    
    # get queue from the old Netflix account and print it 
    my $queue = $old_netflix->getQueue();  
    print Dumper( $queue );
    
    # log into a new Netflix account
    my $new_netflix = WWW::Netflix->new();
    $new_netflix->login( 'USERNAME', 'PASSWORD' );
    
    # copy all ratings from the old account to the new one
    foreach my $movie ( keys %$ratings ) {
        $new_netflix->setRating( $movie, $old_netflix->getRating( $movie ) );
    }

    # copy queue from the old account to the new one
    foreach my $movie ( @{ $queue->{ queued } }, 
                        @{ $queue->{ saved } } ) {
        my ( $id, $title ) = @$movie;
        $new_netflix->queueMovie( $id );
    }
    
=over 4

=item B<new>

    my $netflix = WWW::Netflix->new();
    
Instantiates an object with which to perform further requests. 

=item B<login>

    $netflix->login( $username, $password );

Login is required in order to retreive the ratings and queue.

=over 8

=item $username

the username you use to login to your Netflix account

=item $password

the password for your Netflix account

=back

=item B<getRatings>

    $netflix->getRatings();
    
Returns a reference to a hashref of all rated Netflix movies for the
account. It may take a little while, as it has to scrape quite a few
pages in order to acheive the final result.

    {
      '1007395' => {
                     'title' => 'A_Streetcar_Named_Desire',
                     'rating' => '4'
                   },
      # ...
    };


=item B<getQueue>

    $netflix->getQueue();
    
Retrieves a reference to a hashref of all movies in the queue for the
Netflix account. It may take a while to gather all of the movies in
the queue.

    {
        queued => [
            [ 12345, 'A neat movie' ],
            # ...
        ],
        saved  => [
            [ 666789, 'A Movie That Netflix Might Stock Someday' ]
            # ...
        ]
        home   => [
            [ 987765, 'Best Movie Ever' ]
            # ...
        ]
    }

=item B<setRating>

    $netflix->setRating( $movie_id, $rating );
    
Sets a rating for a particular movie.  

=over 8

=item $movie_id

a numerical Netflix movie ID number

=item $rating

a single-digit star rating (1-5)

=back


=item B<queueMovie>

    $netflix->queueMovie( $movie_id );
    
Puts a particular movie in the queue.

=over 8

=item $movie_id

a numerical Netflix movie ID number

=back


=item B<getRating>

    $netflix->getRating( $movie_id );
    
Gets a rating for a particular movie. 

=over 8

=item $movie_id

an 8-digit Netflix movie ID number

=back

=item B<getTitle>

    $netflix->getTitle( $movie_id );
    
Gets a title for a particular movie.

=over 8

=item $movie_id

a numerical Netflix movie ID number

=back

=back

=head1 AUTHORS

Colin Meyer and Christie Robertson E<lt>pants@helvella.orgE<gt>

WWW-Netflix 0.05 is based on Net-Netflix 0.03 by John Resig.

=head1 DISCLAIMER

This application utilitizes screen-scraping techniques, which are very
fickle and susceptable to changes.

=head1 COPYRIGHT

Copyright 2008 Christie Robertson and Colin Meyer. 
Copyright 2005 John Resig

=head1 LICENSE

This program is free software; you can redistribute it and/or modify it
under the same terms as Perl itself.

See <http://www.perl.com/perl/misc/Artistic.html>

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

=cut
