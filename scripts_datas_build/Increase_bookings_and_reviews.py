# scripts_datas_build/Increase_bookings_and_reviews.py
import pandas as pd
import random
from datetime import datetime, timedelta
import os

def increase_bookings_and_reviews():

    # Chargement des données utilisateurs et logements
    users = pd.read_csv('datas/users.csv')
    properties = pd.read_csv('datas/properties.csv')  # doit contenir 'property_id' et 'price_per_night'

    # Load existing data
    bookings_file = 'datas/bookings.csv'
    reviews_file = 'datas/reviews.csv'

    if os.path.exists(bookings_file):
        bookings_csv = pd.read_csv(bookings_file)
        max_booking_id = bookings_csv['booking_id'].max()
    else:
        bookings_csv = pd.DataFrame()
        max_booking_id = 0

    if os.path.exists(reviews_file):
        reviews_csv = pd.read_csv(reviews_file)
        max_review_id = reviews_csv['review_id'].max()
    else:
        reviews_csv = pd.DataFrame()
        max_review_id = 0

    # Combien de bookings/reviews tu veux générer ?
    NUM_BOOKINGS = 10000
    NUM_REVIEWS = 9000

    # Fonctions utilitaires
    def random_date(start, end):
        """Retourne une date aléatoire entre deux dates"""
        return start + timedelta(days=random.randint(0, (end - start).days))

    def generate_booking_dates(booking_date):
        """
        Génère une start_date entre 1 et 182 jours après la booking_date,
        puis une end_date entre 1 et 21 nuits après la start_date.
        """
        start_date = booking_date + timedelta(days=random.randint(1, 182))
        nights = random.randint(1, 21)
        end_date = start_date + timedelta(days=nights)
        return start_date, end_date, nights

    def generate_review_date(end_date):
        """Génère une date de review entre 1 jour et 1 mois après le end_date"""
        delta_days = random.randint(1, 30)
        return end_date + timedelta(days=delta_days)

    def generate_review_text(rating):
        if rating >= 4:
            return random.choice([
                "Séjour incroyable, merci !", 
                "Tout était parfait ", 
                "Très bonne expérience", 
                "Rien à redire",
                "Super expérience !",
                "Très bon séjour",
                "Propriétaire sympa et logement clean",
                "Je recommande !",
                "Super séjour, hôte très sympa !",
                "Excellente expérience, je recommande.",
                "Le logement était parfait",
                "Top top top ! Rien à redire."
            ])
        elif rating == 3:
            return random.choice([
                "C'était moyen", 
                "Un peu décevant", 
                "Pas mal mais peut mieux faire",
                "Correct sans plus",
                "Peut mieux faire",
                "C'était ok",
                "Juste correct mais sans plus.",
                "Quelques soucis, mais globalement ok.",
                "Moyennement satisfait."
            ])
        else:
            return random.choice([
                "Expérience bof", 
                "Beaucoup de problèmes", 
                "Très déçu",
                "Expérience décevante",
                "Propreté douteuse",
                "Je ne recommande pas",
                "Propriétaire peu accueillant !",
                "Très déçu, pas conforme à l'annonce.",
                "Problèmes d'hygiène, je ne recommande pas.",
                "Expérience frustrante, à éviter."
            ])
        
    # Dictionnaire pour suivre les plages de réservations déjà prises par propriété
    existing_bookings = {}

    # Initialiser avec les bookings déjà présents (si existants)
    for _, row in bookings_csv.iterrows():
        pid = row['property_id']
        start = pd.to_datetime(row['start_date'])
        end = pd.to_datetime(row['end_date'])
        existing_bookings.setdefault(pid, []).append((start, end))

    # Génération des bookings
    bookings = []
    for i in range(NUM_BOOKINGS):
        booking_id = max_booking_id + i + 1
        user_id = random.choice(users['user_id'].values)
        user_row = users[users['user_id'] == user_id].iloc[0]
        signup_date = datetime.strptime(user_row['signup_date'], "%Y-%m-%d")
        # Générer booking_date entre signup_date +1 jour et signup_date + 90 jours
        booking_date = signup_date + timedelta(days=random.randint(1, 90))

        # Filtrer les logements qui ne sont pas à ce user
        available_properties = properties[properties['owner_id'] != user_id]
        # Si aucun logement dispo (très rare), on skip
        if available_properties.empty:
            continue
        property_row = available_properties.sample().iloc[0]
        property_id = property_row['property_id']
        price_per_night = property_row['price_per_night']
        
        # Empêcher le chevauchement de réservations
        attempts = 0
        max_attempts = 10
        while attempts < max_attempts:
            start_date, end_date, nights = generate_booking_dates(booking_date)
            # Récupérer les bookings existants pour cette propriété
            bookings_for_property = existing_bookings.get(property_id, [])
        
            # Vérifier s'il y a un chevauchement
            overlap = any(
                not (end_date <= existing_start or start_date >= existing_end)
                for existing_start, existing_end in bookings_for_property
            )

            if not overlap:
                # Pas de chevauchement, on peut valider
                break
            attempts += 1
        else:
            # Si on n'a pas réussi à éviter le chevauchement après plusieurs essais, on skip
            continue

        # Enregistrer les dates comme existantes pour la propriété
        existing_bookings.setdefault(property_id, []).append((start_date, end_date))
        
        total_price = round(price_per_night * nights, 2)
        bookings.append([booking_id, user_id, property_id, start_date.date(), end_date.date(), total_price, booking_date.date()])

    bookings_df = pd.DataFrame(bookings, columns=[
        'booking_id', 'user_id', 'property_id', 'start_date', 'end_date', 'total_price', 'booking_date'
    ])

    # Tirer aléatoirement des bookings uniques pour lesquels on va générer une review
    bookings_with_reviews = random.sample(bookings, NUM_REVIEWS)

    # Génération des reviews
    reviews = []
    for i,booking in enumerate(bookings_with_reviews):
        review_id = max_review_id + i + 1
        booking_id = booking[0]
        rating = random.randint(1, 5)
        comment = generate_review_text(rating)
        review_date = generate_review_date(datetime.strptime(str(booking[4]), "%Y-%m-%d")).date()
        
        reviews.append([review_id, booking_id, rating, comment, review_date])

    reviews_df = pd.DataFrame(reviews, columns=[
        'review_id', 'booking_id', 'rating', 'comment', 'review_date'
    ])

    bookings_combined = pd.concat([bookings_csv, bookings_df], ignore_index=True)
    reviews_combined = pd.concat([reviews_csv, reviews_df], ignore_index=True)

    # Sauvegarde
    bookings_combined.to_csv('datas/bookings.csv', index=False)
    reviews_combined.to_csv('datas/reviews.csv', index=False)

    print("Données enrichies et ajoutées dans bookings.csv et reviews.csv")

    return None