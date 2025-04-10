# from django import forms
#
# from .models import Category
#
#
# class StationForm(forms.Form):
#     category = forms.ChoiceField(choices=[], label="Kategoria")
#     stations = forms.IntegerField(min_value=1, label="Liczba stanowisk")
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields["category"].choices = [
#             (category.name, category.name.replace("_", " "))
#             for category in Category.objects.all()
#         ]



# views.py
# from django.shortcuts import render
#
# from .forms import StationForm
# from .models import Category, Player
#
#
# def generate_start_list(request):
#     if request.method == "POST":
#         form = StationForm(request.POST)
#         if form.is_valid():
#             category_name = form.cleaned_data["category"]
#             stations = form.cleaned_data["stations"]
#
#             category = Category.objects.get(name=category_name)
#             players = Player.objects.filter(categories=category).order_by(
#                 "surname", "name"
#             )
#             player_count = players.count()
#
#             if stations == 0:
#                 form.add_error("stations", "Liczba stanowisk musi być większa od 0.")
#                 return render(request, "station_form.html", {"form": form})
#
#             if player_count == 0:
#                 return render(
#                     request,
#                     "start_list.html",
#                     {
#                         "message": f"Brak zawodników w kategorii {category_name}.",
#                         "category": category_name,
#                         "stations": stations,
#                     },
#                 )
#
#             players_per_station = (player_count + stations - 1) // stations
#             stations_list = [
#                 {
#                     "station_number": i + 1,
#                     "players": players[
#                         i * players_per_station : (i + 1) * players_per_station
#                     ],
#                 }
#                 for i in range(stations)
#             ]
#
#             return render(
#                 request,
#                 "start_list.html",
#                 {
#                     "stations_list": stations_list,
#                     "stations": stations,
#                     "category": category_name,
#                 },
#             )
#     else:
#         form = StationForm()
#
#     return render(request, "station_form.html", {"form": form})

#start_list.html
# <!DOCTYPE html>
# <html lang="pl">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Lista startowa - {{ category }}</title>
#     <style>
#         body {
#             font-family: Arial, sans-serif;
#             line-height: 1.6;
#             margin: 0;
#             padding: 20px;
#         }
#         h1, h2, h3 {
#             color: #333;
#         }
#         table {
#             border-collapse: collapse;
#             width: 100%;
#             margin-bottom: 20px;
#         }
#         th, td {
#             border: 1px solid #ddd;
#             padding: 8px;
#             text-align: left;
#         }
#         th {
#             background-color: #f2f2f2;
#             font-weight: bold;
#         }
#         tr:nth-child(even) {
#             background-color: #f9f9f9;
#         }
#     </style>
# </head>
# <body>
#     <h1>Lista startowa dla kategorii {{ category }}</h1>
#
#     <h2>Liczba stanowisk: {{ stations }}</h2>
#
#     {% if message %}
#         <p>{{ message }}</p>
#     {% else %}
#         {% for station in stations_list %}
#             <h3>Stanowisko {{ station.station_number }}</h3>
#             <table>
#                 <thead>
#                     <tr>
#                         <th>Nazwisko</th>
#                         <th>Imię</th>
#                     </tr>
#                 </thead>
#                 <tbody>
#                     {% for player in station.players %}
#                         <tr>
#                             <td>{{ player.surname }}</td>
#                             <td>{{ player.name }}</td>
#                         </tr>
#                     {% endfor %}
#                 </tbody>
#             </table>
#         {% endfor %}
#     {% endif %}
# </body>
# </html>

#station_form.html

# <form method="POST">
#     {% csrf_token %}
#     {{ form.as_p }}
#     <button type="submit">Generate Start List</button>
# </form>
