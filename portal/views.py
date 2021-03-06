import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render

from portal.models import Order, Invoice, Recipe, RecipeList
from .forms import *
from django.urls import reverse
from django.contrib.auth.models import User
from django.views import generic


# Create your views here.
# für die Berechtigungsüberprüfung können diese Decorator verwendet werden:
# @login_required ODER @permission_required('portal.<permissionName>')


def index(request):
    """
    View function for home page of site.
    """
    # variables for context
    num_customers = UserProfile.objects.all().count()
    # Number of visits to this view, as counted in the session variable.
    # num_visits = request.session.get('num_visits', 0)
    # request.session['num_visits'] = num_visits + 1

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'index.html',
        context={'num_customers': num_customers}
    )


def register(request):
    if request.method == 'POST':
        user_creation_form = UserCreationForm(request.POST)
        user_info_form = UserInformationForm(request.POST, prefix='user_info')
        user_profile_form = UserProfileForm(request.POST, prefix='user_profile')
        if user_creation_form.is_valid() * user_info_form.is_valid() * user_profile_form.is_valid():
            # user = user_creation_form.save()
            new_user = User(
                username=user_creation_form.cleaned_data['username'],
                first_name=user_info_form.cleaned_data['first_name'],
                last_name=user_info_form.cleaned_data['last_name'],
                email=user_info_form.cleaned_data['email']
            )
            new_user.set_password(raw_password=user_creation_form.cleaned_data['password2'])
            new_user.save()
            user_profile = user_profile_form.save(commit=False)
            user_profile.user = new_user
            user_profile.save()
            return HttpResponseRedirect(reverse('registration_complete'))
    else:
        user_creation_form = UserCreationForm()
        user_info_form = UserInformationForm(prefix='user_info')
        user_profile_form = UserProfileForm(prefix='user_profile')
    return render(request, 'registration/registration_form.html',
                  context={
                      'user_form': user_creation_form,
                      'user_info_form': user_info_form,
                      'user_profile_form': user_profile_form,
                  })


def registration_complete(request):
    return render(
        request,
        'registration/registration_complete.html'
    )


@login_required
def add_recipe(request):
    if request.method == 'POST':
        recipe_form = RecipeForm(request.POST)

        if recipe_form.is_valid():
            new_recipe = Recipe(
                rezept_bezeichnung=recipe_form.cleaned_data['rezept_bezeichnung'],
                benutzer=request.user
            )
            new_recipe.save()

            return HttpResponseRedirect('recipe_ingredients?id=' + str(new_recipe.id))
    else:
        recipe_form = RecipeForm()
    return render(request, 'portal/add_recipe_form.html',
                  context={
                      'recipe_form': recipe_form
                  })


@login_required
def add_ingredient(request):
    if request.GET['id'] and request.GET['id'].isdigit():
        current_recipe = Recipe.objects.get(id=int(request.GET['id']))
        recipe_lists = RecipeList.objects.filter(recipe=current_recipe)
        if request.method == 'POST':

            recipe_list_form = RecipeListForm(request.POST)

            if recipe_list_form.is_valid():
                new_recipe_list = RecipeList(
                    recipe=current_recipe,
                    ingredient=recipe_list_form.cleaned_data['ingredient'],
                    amount=recipe_list_form.cleaned_data['amount']
                )
                new_recipe_list.save()
    return render(request, 'portal/recipe_ingredients.html',
                  context={
                      'recipe_list_form': RecipeListForm(),
                      'recipe_lists': recipe_lists,
                      'receipe': current_recipe,
                  })


class RecipesView(generic.ListView):
    model = Recipe
    template_name = '../../portal/templates/portal/recipe_list.html'
    # alternativ in einem eigenen Ordner (recipes) in templates: template_name = 'recipes/recipe_list.html'



@login_required
def show_recepies(request):
    object_list = Recipe.objects.filter(benutzer=request.user)
    return render(request, 'portal/recipe_list.html', context={'object_list': object_list})


@login_required
def order(request):
    OrderFormset = formset_factory(OrderForm, extra=10)
    if request.method == 'POST':
        formset = OrderFormset(request.POST)
        if formset.is_valid():
            resultString = 'Bitte geben Sie mindestens eine Bestellung in die Bestellzeilen ein.'
            if formset.has_changed():
                new_order = Order(kunde=request.user, bestell_datum=datetime.datetime.now())
                new_order.save()
                new_invoice = Invoice(
                    order=new_order,
                    rechnungs_datum=datetime.datetime.now(),
                    bezahl_status='offen',
                    rechnungs_summe=0
                )
                resultString = 'Bestellung erfolgreich. Ihre Bestellungsnummer ist: ' + str(new_order.id) + "."
                for form in formset:
                    recipe_id = form.cleaned_data.get('rezept')
                    amount = form.cleaned_data.get('menge')
                    if recipe_id and amount:
                        recipe_ingredients = RecipeList.objects.filter(recipe=recipe_id)
                        for recipe_list in recipe_ingredients:
                            new_invoice.rechnungs_summe += \
                                float(amount) * recipe_list.amount * recipe_list.ingredient.price_per_unit
                        OrderPosition(
                            bestellung=new_order,
                            rezept=recipe_id,
                            menge=amount,
                            als_teig=form.cleaned_data.get('als_teig')
                        ).save()
                new_invoice.rechnungs_summe = round(new_invoice.rechnungs_summe, 2)
                new_invoice.save()
        return render(
            request,
            'portal/order_processing.html',
            context={'order_result': resultString,
                     }
        )
    else:
        return render(
            request,
            'portal/order_form.html',
            context={'order_form': OrderFormset()}
        )


@login_required
def myorders(request):
    orders = Order.objects.filter(kunde=request.user)
    return render(
        request,
        'portal/myorders.html',
        context={'myorders': orders}
    )


@login_required
def myinvoices(request):
    invocies = Invoice.objects.filter(order__kunde=request.user)
    return render(
        request,
        'portal/myinvoices.html',
        context={'myinvoices': invocies}
    )


@login_required
def invoicedetail(request):
    if request.GET['id'] and request.GET['id'].isdigit():
        invoice = Invoice.objects.get(id=int(request.GET['id']))
        if invoice.order.kunde == request.user:
            order_positions = OrderPosition.objects.filter(bestellung=invoice.order)
            thankyoutext = ''
            if request.method == 'POST':
                invoice.bezahl_status = 'bezahlt'
                invoice.save()
                thankyoutext = 'Vielen Dank, dass Sie BakeryPortal gewählt haben.'
            return render(
                request,
                'portal/invoice_detail.html',
                context={'invoice': invoice,
                         'orderposition': order_positions,
                         'mwst': round(invoice.rechnungs_summe * 0.19, 2),
                         'total': round(invoice.rechnungs_summe * 1.19, 2),
                         'thankyoutext': thankyoutext}
            )
    return render(
        request,
        'portal/invoice_detail.html',
    )