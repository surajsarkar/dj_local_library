from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
import uuid
import datetime
from ..models import Author, BookInstance, Book, Genre, Language
# Create your tests here.


class AuthorListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        number_of_authors = 14

        for author_id in number_of_authors:
            Author.objects.create(
                first_name = f'Kassy{author_id}',
                last_name=f'cuky{author_id}',
            )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/catalog/authors/')
        self.assertEquals(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('authors'))
        self.assertEquals(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('authors'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        response = self.client.get(reverse('authors'))
        self.assertEquals(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertEquals(len(response.context['author_list']), 3)


class LoanedBookInstancesByUserListViewTest(TestCase):
    def setUp(self):
        test_user1 = User.objects.create_user( username='testuser1', password='1X<ISRUkw+tuK' )
        test_user2 = User.objects.create_user( username='testuser2', password='2HJ1vRV0Z&3iD' )

        test_user1.save()
        test_user2.save()

        # creating a book

        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name="English")
        test_book = Book.objects.create(
            title='Book Title',
            summary='My book summary',
            isbn='ABCDEFG',
            author=test_author,
            language=test_language,
        )

        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(response, '/accounts/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        self.assertEquals(str(response.context['user']), 'testuser1')

        self.assertEquals(response.status_code, 200)

        self.assertTemplateUsed(response, 'catalog/bookinstance_list_borrowed_user.html')

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # checking user
        self.assertEquals(str(response.context['user']), 'testuser1')
        # checking status code
        self.assertEquals(response.status_code, 200)


        # Now change all books to be on loan
        books = BookInstance.objects.all()[:10]

        for book in books:
            book.status = 'o'
            book.save()

        # Check that now we have borrowed books in the list

        self.assertEqual(response.status_code, 200)

        self.assertTrue('bookinstance_list' in response.context)

        # Confirm all books belong to testuser1 and are on loan
        for bookitem in response.context['bookinstance_list']:
            self.assertEqual(response.context['user'], bookitem.borrower)
            self.assertEqual(bookitem.status, 'o')

    def test_pages_ordered_by_due_date(self):
        for book_item in BookInstance.objects.all():
            book.status = 'o'
            book.save()

        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        self.assertEqual(str(response.context['user']), 'testuser1')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['bookinstance_list']), 10)

        last_date = 0

        for book in response.context['bookinstance_list']:

            if last_date == 0:
                last_date = book.due_back
            else:
                self.assertTrue(last_date < book.due_back)
                last_date = book.due_back


class RenewBookInstancesViewTest(TestCase):

    def setUp(self):
        test_user1 = User.objects.create(first_name='testuser1', password='1X<ISRUkw+tuK')
        test_user2 = User.objects.create(first_name='testuser2', password='1X<ISRUkw+tuK')

        test_user1.save()
        test_user2.save()

        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()


        # create a book

        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.object.create(name='English')
        test_book = Book.objects.create(
            title='Book Title',
            summery='My book summery',
            isbn='ABCDEFG',
            author=test_author,
            language=test_language,
        )


        # creating genre for test book

        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        # Create a BookInstance object for test_user1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2016',
            due_back=return_date,
            borrower=test_user1,
            status='o'
        )

        # create book instance for user 1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance2 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2016',
            due_back=return_date,
            borrower=test_user2,
            status='o'
        )

    def test_redirect_if_not_logged_in(self) :
        response = self.client.get( reverse( 'renew-book-librarian', kwargs={'pk' : self.test_bookinstance1.pk} ) )
        # Manually check redirect (Can't use assertRedirect, because the redirect URL is unpredictable)
        self.assertEqual( response.status_code, 302 )
        self.assertTrue( response.url.startswith( '/accounts/login/' ) )

    def test_forbidden_if_logged_in_but_not_correct_permission(self) :
        login = self.client.login( username='testuser1', password='1X<ISRUkw+tuK' )
        response = self.client.get( reverse( 'renew-book-librarian', kwargs={'pk' : self.test_bookinstance1.pk} ) )
        self.assertEqual( response.status_code, 403 )

    def test_logged_in_with_permission_borrowed_book(self) :
        login = self.client.login( username='testuser2', password='1X<ISRUkw+tuK' )
        response = self.client.get( reverse( 'renew-book-librarian', kwargs={'pk' : self.test_bookinstance2.pk} ) )

        # Check that it lets us login - this is our book and we have the right permissions.
        self.assertEqual( response.status_code, 200 )

    def test_logged_in_with_permission_another_users_borrowed_book(self) :
        login = self.client.login( username='testuser2', password='1X<ISRUkw+tuK' )
        response = self.client.get( reverse( 'renew-book-librarian', kwargs={'pk' : self.test_bookinstance1.pk} ) )

        # Check that it lets us login. We're a librarian, so we can view any users book
        self.assertEqual( response.status_code, 200 )

    def test_HTTP404_for_invalid_book_if_logged_in(self) :
        # unlikely UID to match our bookinstance!
        test_uid = uuid.uuid4()
        login = self.client.login( username='testuser2', password='1X<ISRUkw+tuK' )
        response = self.client.get( reverse( 'renew-book-librarian', kwargs={'pk' : test_uid} ) )
        self.assertEqual( response.status_code, 404 )

    def test_uses_correct_template(self) :
        login = self.client.login( username='testuser2', password='1X<ISRUkw+tuK' )
        response = self.client.get( reverse( 'renew-book-librarian', kwargs={'pk' : self.test_bookinstance1.pk} ) )
        self.assertEqual( response.status_code, 200 )

        # Check we used correct template
        self.assertTemplateUsed( response, 'catalog/book_renew_librarian.html' )

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        login = self.client.login(username='testuser2', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(response.status_code, 200)

        date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(weeks=3)
        self.assertEqual(response.coxtext['form'].initial('renewal_date'), date_3_weeks_in_future)

    def test_redirects_to_all_borrowed_book_list_on_success(self):
        login = self.client.login(username='testuser2', passowrd='1X<ISRUkw+tuK')
        valid_date_on_future = datetime.date.today() + datetime.timedelta(weeks=2)
        response = self.client.post(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}), {'renewal_date': valid_date_on_future})
        self.assertRedirects(response, reverse('all-borrowed'))

    def test_form_invalid_renewal_date_past(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
        response = self.client.post(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}), {'renewal_date': date_in_past})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'renewal_date', 'Invalid date - renewal in past')

    def test_form_invalid_renewal_date_future(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        response = self.client.post(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}), {'renewal_date': invalid_date_in_future})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'renewal_date', 'Invalid date - renewal more than 4 weeks ahead')
