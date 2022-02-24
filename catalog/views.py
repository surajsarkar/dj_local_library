import datetime

from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from .models import Book, BookInstance, Genre, Author
from .forms import RenewBookForm
# Create your views here


def index(request):

    """View function for home page of site."""
    # Generate counts of some of the main objects

    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_book_instances = Book.objects.filter(title__icontains='the').count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default.

    num_authors = Author.objects.count()

    # counting all genre
    num_genre = Genre.objects.count()

    # Number of visits to this view, as counted in the session variable.

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genre': num_genre,
        'num_book_instances': num_book_instances,
        'num_visits': num_visits,

    }

    # Render the HTML template index.html with the data in the context variable

    return render(request, 'index.html', context)


class BookListView(generic.ListView):
    model = Book
    paginate_by = 2
    # context_object_name = 'my_book_list'  # Setting custom name for template variable in class based view
    # queryset = Book.objects.filter(title__icontains=='the')
    # template_name = 'book/book_template.html'


class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class AllBooksOnLoan(PermissionRequiredMixin, generic.ListView):
    permission_required = 'can_mark_return'
    model = BookInstance
    template_name = 'catalog/all_bookinstance_borrowed.html'

    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@login_required
@permission_required('catalog.can_mark_return', raise_exception=True)
def renew_book_librarian(request, pk):

    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == "POST":

        form = RenewBookForm(request.POST)

        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']

        book_instance.save()

        return HttpResponseRedirect(reverse('all-borrowed'))

    else:

        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

        context = {
            'form': form,
            'book_instance': book_instance,
        }

        return render(request, 'catalog/book_renew_librarian.html', context)


class AuthorCreate(CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/06/2020'}


class AuthorUpdate(UpdateView):
    model = Author
    fields = '__all__'


class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
