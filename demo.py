from tkinter import *
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database="database_project"
    )


def fetch_movies():
    try:
        con = connect_to_db()
        cursor = con.cursor()
        query = "SELECT title, duration, genre, release_date FROM movies"
        cursor.execute(query)
        movies = cursor.fetchall()
        con.close()
        return movies
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return []

def fetch_movie_details(title):
    try:
        con = connect_to_db()
        cursor = con.cursor()
        query = """
            SELECT title, genre, duration, director, actors, rating, release_date
            FROM movies
            WHERE title = %s
        """
        cursor.execute(query, (title,))
        movie_details = cursor.fetchone()
        con.close()
        return movie_details
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None

def fetch_dates_for_movie(title):
    try:
        con = connect_to_db()
        cursor = con.cursor()
        query = """
            SELECT DISTINCT DATE(show_datetime) AS show_date
            FROM showtime
            WHERE movie_id = (SELECT movie_id FROM movies WHERE title = %s)
            ORDER BY show_date
        """
        cursor.execute(query, (title,))
        dates = cursor.fetchall()
        con.close()
        return [date[0].strftime('%Y-%m-%d') for date in dates]
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return []

def fetch_times_for_movie(title, selected_date):
    try:
        con = connect_to_db()
        cursor = con.cursor()
        query = """
            SELECT TIME(show_datetime) AS show_time
            FROM showtime
            WHERE movie_id = (SELECT movie_id FROM movies WHERE title = %s)
              AND DATE(show_datetime) = %s
            ORDER BY show_time
        """
        cursor.execute(query, (title, selected_date))
        times = cursor.fetchall()
        con.close()
        return [str(time[0]) for time in times]
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return []

def fetch_theatres_for_movie(title, selected_date, selected_time):
    try:
        con = connect_to_db()
        cursor = con.cursor()
        query = """
            SELECT t.theatre_name
            FROM showtime s
            JOIN movies m ON s.movie_id = m.movie_id
            JOIN theatre t ON s.theatre_id = t.theatre_id
            WHERE m.title = %s AND DATE(s.show_datetime) = %s AND TIME(s.show_datetime) = %s
        """
        cursor.execute(query, (title, selected_date, selected_time))
        theatres = cursor.fetchall()
        con.close()
        return [theatre[0] for theatre in theatres]
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return []

def user_login():
    global current_user_id

    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        messagebox.showerror("Error", "All fields are required!")
        return

    try:
        con = connect_to_db()
        cursor = con.cursor()

        query = "SELECT user_id FROM users WHERE user_name = %s AND password = %s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        con.close()

        if result:
            current_user_id = result[0]  # current_user_id güncelleniyor
            messagebox.showinfo("Success", "Login successful!")
            film_goruntuleme()
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")

        
def update_seats(ticket_count, movie_title, show_datetime, theatre_name):
    try:
        con = connect_to_db()
        cursor = con.cursor()

        query = """
            SELECT show_id, available_seats
            FROM showtime s
            JOIN movies m ON s.movie_id = m.movie_id
            JOIN theatre t ON s.theatre_id = t.theatre_id
            WHERE m.title = %s AND s.show_datetime = %s AND t.theatre_name = %s
        """
        cursor.execute(query, (movie_title, show_datetime, theatre_name))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "No matching show found for the selected criteria.")
            return

        show_id, available_seats = result
        if ticket_count > available_seats:
            messagebox.showerror("Error", f"Not enough seats available. Only {available_seats} seats left.")
            return

        return show_id
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
        return None
    finally:
        cursor.close()
        con.close()

def finalize_seat_update(ticket_count, show_id):
    try:
        con = connect_to_db()
        cursor = con.cursor()
        call_proc = "CALL UpdateSeats(%s, %s)"
        cursor.execute(call_proc, (ticket_count, show_id))
        con.commit()
        con.close()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
        
def save_booking(show_id, seat_id, total_price, extra_price, ticket_count, status="confirmed"):
    try:
        con = connect_to_db()
        cursor = con.cursor()
        query = """
            INSERT INTO booking (user_id, seat_id, show_id, booking_date, total_price, extra_price, ticket_count, b_status)
            VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s)
        """
        cursor.execute(query, (current_user_id, seat_id, show_id, total_price, extra_price, ticket_count, status))
        con.commit()
        con.close()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")


def payment_simulation(ticket_count, show_id, theatre_name):
    payment_window = Toplevel(root)
    payment_window.title("Payment")
    payment_window.geometry("400x400")

    total_price = ticket_count * 20.0  # Örnek birim fiyat

    Label(payment_window, text="Payment Details", font=("Times New Roman", 16, "bold"), pady=10).pack()

    Label(payment_window, text=f"Total Price: ${total_price:.2f}", font=("Times New Roman", 14), pady=10, fg="green").pack()

    Label(payment_window, text="Card Number:", font=("Times New Roman", 12)).pack(pady=5)
    card_number_entry = Entry(payment_window, font=("Times New Roman", 12))
    card_number_entry.pack(pady=5)

    Label(payment_window, text="Expiry Date (MM/YY):", font=("Times New Roman", 12)).pack(pady=5)
    expiry_date_entry = Entry(payment_window, font=("Times New Roman", 12))
    expiry_date_entry.pack(pady=5)

    Label(payment_window, text="CVV:", font=("Times New Roman", 12)).pack(pady=5)
    cvv_entry = Entry(payment_window, show="*", font=("Times New Roman", 12))
    cvv_entry.pack(pady=5)

    def confirm_payment():
        if not card_number_entry.get() or not expiry_date_entry.get() or not cvv_entry.get():
            messagebox.showerror("Error", "All payment fields are required!")
            return

        seat_id = 1 
        extra_price = 5.0  # Örnek ekstra ücret (VIP vb.)

        finalize_seat_update(ticket_count, show_id)  # Koltuk sayısına göre güncelle
        save_booking(show_id, seat_id, total_price, extra_price, ticket_count)  # current_user_id kullanılıyor
        messagebox.showinfo("Payment Successful", "Your payment has been successfully processed!")
        payment_window.destroy()

    Button(payment_window, text="Pay Now", font=("Times New Roman", 14), bg="green", fg="white",
           command=confirm_payment).pack(pady=20)

    
def book_ticket(title):
    def select_date():
        dates = fetch_dates_for_movie(title)
        if not dates:
            messagebox.showerror("Error", "No dates available for this movie.")
            return

        date_window = Toplevel(root)
        date_window.title("Select Date")
        date_window.geometry("600x400")

        Label(date_window, text="Select a Date:", font=("Times New Roman", 14)).pack(pady=10)
        date_listbox = Listbox(date_window, font=("Times New Roman", 12), height=10)
        for date in dates:
            date_listbox.insert(END, date)
        date_listbox.pack(pady=20)

        def select_time():
            selected_date = date_listbox.get(ACTIVE)
            if not selected_date:
                messagebox.showerror("Error", "Please select a date.")
                return

            times = fetch_times_for_movie(title, selected_date)
            if not times:
                messagebox.showerror("Error", "No times available for the selected date.")
                return

            time_window = Toplevel(date_window)
            time_window.title("Select Time")
            time_window.geometry("600x400")

            Label(time_window, text=f"Select a Time for {selected_date}:", font=("Times New Roman", 14)).pack(pady=10)
            time_listbox = Listbox(time_window, font=("Times New Roman", 12), height=10)
            for time in times:
                time_listbox.insert(END, time)
            time_listbox.pack(pady=20)

            def select_theatre():
                selected_time = time_listbox.get(ACTIVE)
                if not selected_time:
                    messagebox.showerror("Error", "Please select a time.")
                    return

                theatres = fetch_theatres_for_movie(title, selected_date, selected_time)
                if not theatres:
                    messagebox.showerror("Error", "No theatres available for the selected time.")
                    return

                theatre_window = Toplevel(time_window)
                theatre_window.title("Select Theatre")
                theatre_window.geometry("600x400")

                Label(theatre_window, text=f"Select a Theatre for {selected_time}:", font=("Times New Roman", 14)).pack(pady=10)
                theatre_listbox = Listbox(theatre_window, font=("Times New Roman", 12), height=10)
                for theatre in theatres:
                    theatre_listbox.insert(END, theatre)
                theatre_listbox.pack(pady=20)

                def confirm_ticket():
                    selected_theatre = theatre_listbox.get(ACTIVE)
                    if not selected_theatre:
                        messagebox.showerror("Error", "Please select a theatre.")
                        return

                    def ask_ticket_count():
                        count_window = Toplevel(theatre_window)
                        count_window.title("Ticket Count")
                        count_window.geometry("400x300")

                        query = """
                            SELECT available_seats
                            FROM showtime s
                            JOIN movies m ON s.movie_id = m.movie_id
                            JOIN theatre t ON s.theatre_id = t.theatre_id
                            WHERE m.title = %s AND s.show_datetime = %s AND t.theatre_name = %s
                        """
                        con = connect_to_db()
                        cursor = con.cursor()
                        cursor.execute(query, (title, f"{selected_date} {selected_time}", selected_theatre))
                        available_seats = cursor.fetchone()[0]
                        con.close()

                        Label(count_window, text=f"Available Seats: {available_seats}", font=("Times New Roman", 14)).pack(pady=10)
                        Label(count_window, text="Enter Ticket Count:", font=("Times New Roman", 14)).pack(pady=10)
                        ticket_count_entry = Entry(count_window, font=("Times New Roman", 14))
                        ticket_count_entry.pack(pady=10)

                        def finalize_booking():
                            try:
                                ticket_count = int(ticket_count_entry.get())
                                if ticket_count <= 0:
                                    raise ValueError
                                show_id = update_seats(ticket_count, title, f"{selected_date} {selected_time}", selected_theatre)
                                if show_id:
                                    payment_simulation(ticket_count, show_id, selected_theatre)  # 'selected_theatre' burada tiyatro adı
                                count_window.destroy()
                                theatre_window.destroy()
                                time_window.destroy()
                                date_window.destroy()
                            except ValueError:
                                messagebox.showerror("Error", "Please enter a valid ticket count.")
                        Button(count_window, text="Confirm", command=finalize_booking, font=("Times New Roman", 14), bg="green", fg="white").pack(pady=20)

                    ask_ticket_count()

                Button(theatre_window, text="Next", command=confirm_ticket, font=("Times New Roman", 12), bg="blue", fg="white").pack(pady=20)

            Button(time_window, text="Next", command=select_theatre, font=("Times New Roman", 12), bg="blue", fg="white").pack(pady=20)

        Button(date_window, text="Next", command=select_time, font=("Times New Roman", 12), bg="blue", fg="white").pack(pady=20)

    select_date()

def show_reservations():
    global current_user_id

    if current_user_id is None:
        messagebox.showerror("Error", "Please log in to view your reservations.")
        return

    try:
        con = connect_to_db()
        cursor = con.cursor()

        # Rezervasyonları getir
        query = """
            SELECT b.booking_id, m.title AS movie_title, t.theatre_name, s.show_datetime, b.total_price, b.b_status
            FROM booking b
            JOIN showtime s ON b.show_id = s.show_id
            JOIN movies m ON s.movie_id = m.movie_id
            JOIN theatre t ON s.theatre_id = t.theatre_id
            WHERE b.user_id = %s
        """
        cursor.execute(query, (current_user_id,))
        bookings = cursor.fetchall()
        con.close()

        reservation_window = Toplevel(root)
        reservation_window.title("My Reservations")
        reservation_window.geometry("900x400")

        Label(reservation_window, text="Your Reservations", font=("Times New Roman", 16, "bold"), pady=10).pack()
        if not bookings:
            Label(reservation_window, text="No reservations found.", font=("Times New Roman", 12)).pack(pady=10)
            return

        frame = Frame(reservation_window)
        frame.pack(fill=BOTH, expand=1, padx=10, pady=10)

        columns = ["Movie Title", "Theatre Name", "Date & Time", "Total Price", "Status", "Action"]
        for idx, col_name in enumerate(columns):
            Label(frame, text=col_name, font=("Times New Roman", 12, "bold"), borderwidth=2, relief="groove").grid(row=0, column=idx, sticky="nsew")

        for row_idx, booking in enumerate(bookings, start=1):
            booking_id, movie_title, theatre_name, show_datetime, total_price, status = booking
            for col_idx, value in enumerate(booking[1:]):
                Label(frame, text=value, font=("Times New Roman", 12), borderwidth=2, relief="groove").grid(row=row_idx, column=col_idx, sticky="nsew")

            # Eğer durum 'cancelled' değilse iptal butonu ekle
            if status != "cancelled":
                Button(frame, text="Cancel", font=("Times New Roman", 12), bg="dark red", fg="white",
                       command=lambda b_id=booking_id: cancel_booking(b_id)).grid(row=row_idx, column=len(columns) - 1, sticky="nsew")
            else:
                Label(frame, text="Cancelled", font=("Times New Roman", 12), fg="gray", borderwidth=2, relief="groove").grid(row=row_idx, column=len(columns) - 1, sticky="nsew")

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")



def cancel_booking(booking_id):
    try:
        con = connect_to_db()
        cursor = con.cursor()

        # İptal edilen bilet bilgilerini al
        query = """
            SELECT b.show_id, b.ticket_count, b.b_status
            FROM booking b
            WHERE b.booking_id = %s
        """
        cursor.execute(query, (booking_id,))
        result = cursor.fetchone()

        if not result or result[2] == "cancelled":
            messagebox.showerror("Error", "Booking already cancelled or not found.")
            return

        show_id, cancelled_tickets, _ = result

        # Rezervasyonu iptal et
        query_update = """
            UPDATE booking
            SET b_status = 'cancelled'
            WHERE booking_id = %s
        """
        cursor.execute(query_update, (booking_id,))

        # Prosedürü çağırarak koltukları geri ekle
        query_proc = "CALL UpdateSeatsOnCancellation(%s, %s)"
        cursor.execute(query_proc, (cancelled_tickets, show_id))

        con.commit()
        messagebox.showinfo("Success", "Your booking has been successfully cancelled!")
        show_reservations()

    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"An error occurred while cancelling your booking: {err}")

    finally:
        cursor.close()
        con.close()

poster_paths = {
        "Gladiator II": r"C:\\Users\\dilar\\OneDrive\\Masaüstü\\first_part\\posters\\Gladiator_II.png",
        "Moana 2": r"C:\\Users\\dilar\\OneDrive\\Masaüstü\\first_part\\posters\\Moana_2.png",
        "The Bell Keeper": r"C:\\Users\\dilar\\OneDrive\\Masaüstü\\first_part\\posters\\The_Bell_Keeper.png",
        "Here": r"C:\\Users\\dilar\\OneDrive\\Masaüstü\\first_part\\posters\\Here.png",
        "The Last Breath": r"C:\\Users\\dilar\\OneDrive\\Masaüstü\\first_part\\posters\\The_Last_Breath.png",
        "Wicked": r"C:\\Users\\dilar\\OneDrive\\Masaüstü\\first_part\\posters\\Wicked.png"
    }

# Movie details window setup
def show_movie_details(title):
    movie_details = fetch_movie_details(title)
    if not movie_details:
        messagebox.showerror("Error", "Details for this movie could not be retrieved.")
        return

    details_window = Toplevel(root)
    details_window.title(f"Details - {title}")
    details_window.geometry("650x650")

    details_frame = Frame(details_window, bg="black")
    details_frame.place(relwidth=1, relheight=1)

    poster_frame = Frame(details_frame, bg="black")
    poster_frame.grid(row=0, column=0, padx=20, pady=20)

    info_frame = Frame(details_frame, bg="black")
    info_frame.grid(row=1, column=0, padx=20, pady=10)

    button_frame = Frame(details_frame, bg="black")
    button_frame.grid(row=0, column=1, rowspan=2, padx=20, pady=20, sticky=N)

    poster_path = poster_paths.get(title, None)
    if poster_path:
        try:
            poster_image = Image.open(poster_path)
            poster_image = poster_image.resize((250, 300))
            photo = ImageTk.PhotoImage(poster_image)
            poster_label_frame = Frame(poster_frame, bg="black")
            poster_label_frame.pack()
            Label(poster_label_frame, text=title, font=("Times New Roman", 14, "bold"), fg="white", bg="black").pack()
            poster_label = Label(poster_label_frame, image=photo, bg="black")
            poster_label.image = photo
            poster_label.pack()
        except FileNotFoundError:
            Label(poster_frame, text="No Poster Available", fg="white", bg="black", font=("Times New Roman", 12)).pack()

    details = {
        "Genre": movie_details[1],
        "Duration": f"{movie_details[2]} min",
        "Director": movie_details[3],
        "Actors": movie_details[4],
        "IMDB Rating": movie_details[5],
        "Release Date": movie_details[6].strftime('%Y-%m-%d')
    }

    for key, value in details.items():
        frame = Frame(info_frame, bg="black")
        frame.pack(anchor=W, pady=2)
        Label(frame, text=f"{key}: ", font=("Times New Roman", 12, "bold"), fg="white", bg="black").pack(side=LEFT)
        Label(frame, text=value, font=("Times New Roman", 12), fg="white", bg="black").pack(side=LEFT)

    Button(details_frame, text="Buy Ticket", bg="gray", fg="white", font=("Times New Roman", 16, "bold"),
           command=lambda: book_ticket(title))\
        .place(x=370, y=300)

# Movie viewer window
def film_goruntuleme():
    movie_window = Toplevel(root)
    movie_window.title("Movie Viewer")
    movie_window.geometry("900x800")
    
    try:
        background_image = Image.open(r"C:\\Users\\dilar\\OneDrive\\Masaüstü\\background2.jpeg")
        background_image = background_image.resize((900, 800))
        bg = ImageTk.PhotoImage(background_image)
        bg_label = Label(movie_window, image=bg)
        bg_label.image = bg
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except FileNotFoundError:
        messagebox.showerror("Error", "Background image file not found. Please ensure the path is correct.")

    Button(movie_window, text="My Reservations", command=show_reservations, font=("Times New Roman", 12), bg="green", fg="white").place(x=612, y=50)
    movies = fetch_movies()

    if not movies:
        messagebox.showerror("Error", "No movies found in the database!")
        return

    movie_frame = Frame(movie_window, bg="black")
    movie_frame.place(relx=0.5, rely=0.55, anchor=CENTER)

    for idx, movie in enumerate(movies):
        title, duration, genre, release_date = movie
        row = idx // 3
        column = idx % 3

        poster_path = poster_paths.get(title, None)
        if poster_path:
            try:
                poster_image = Image.open(poster_path)
                poster_image = poster_image.resize((142, 192))
                photo = ImageTk.PhotoImage(poster_image)
                poster_label = Label(movie_frame, image=photo, bg="black", cursor="hand2")
                poster_label.image = photo
                poster_label.grid(row=row * 3, column=column, padx=30, pady=20)
                poster_label.bind("<Button-1>", lambda e, t=title: show_movie_details(t))
            except FileNotFoundError:
                Label(movie_frame, text="No Image", font=("Times New Roman", 10), fg="white", bg="black").grid(row=row * 3, column=column, padx=30, pady=20)

        title_label = Label(movie_frame, text=title, font=("Times New Roman", 12, "bold"), fg="white", bg="black")
        title_label.grid(row=row * 3 + 1, column=column, padx=30, pady=(10, 0))

        details_label = Label(movie_frame, text=f"{duration} min\n{genre}", font=("Times New Roman", 12), fg="gray", bg="black")
        details_label.grid(row=row * 3 + 2, column=column, padx=30, pady=(0, 10))

# Add a movie to the database
def add_movie():
    def save_movie():
        title = entry_title.get()
        genre = entry_genre.get()
        duration = entry_duration.get()
        release_date = entry_release_date.get()

        if not title or not genre or not duration or not release_date:
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            con = connect_to_db()
            cursor = con.cursor()
            query = "INSERT INTO movies (title, genre, duration, release_date) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (title, genre, duration, release_date))
            con.commit()
            con.close()
            messagebox.showinfo("Success", "Movie added successfully!")
            add_window.destroy()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Database error: {err}")

    add_window = Toplevel(root)
    add_window.title("Add Movie")
    add_window.geometry("530x320")

    Label(add_window, text="Title:", font=("Times New Roman", 12)).place(x=50, y=50)
    entry_title = Entry(add_window, font=("Times New Roman", 12))
    entry_title.place(x=260, y=50, width=200)

    Label(add_window, text="Genre:", font=("Times New Roman", 12)).place(x=50, y=100)
    entry_genre = Entry(add_window, font=("Times New Roman", 12))
    entry_genre.place(x=260, y=100, width=200)

    Label(add_window, text="Duration (min):", font=("Times New Roman", 12)).place(x=50, y=150)
    entry_duration = Entry(add_window, font=("Times New Roman", 12))
    entry_duration.place(x=260, y=150, width=200)

    Label(add_window, text="Release Date (YYYY-MM-DD):", font=("Times New Roman", 12)).place(x=50, y=200)
    entry_release_date = Entry(add_window, font=("Times New Roman", 12))
    entry_release_date.place(x=260, y=200, width=200)

    Button(add_window, text="Add", command=save_movie, font=("Times New Roman", 12), bg="#458b00", fg="white").place(x=310, y=250, width=100)

# Delete a movie from the database
def delete_movie():
    movies = fetch_movies()
    if not movies:
        messagebox.showerror("Error", "No movies available for deletion.")
        return

    delete_window = Toplevel(root)
    delete_window.title("Delete Movie")
    delete_window.geometry("400x350")

    Label(delete_window, text="Select a movie to delete:", font=("Times New Roman", 12)).pack(pady=10)
    movie_listbox = Listbox(delete_window, font=("Times New Roman", 12), height=10)
    for movie in movies:
        movie_listbox.insert(END, movie[0])  # Assuming movie title is in index 0
    movie_listbox.pack(pady=10)

    def confirm_deletion():
        selected_movie = movie_listbox.get(ACTIVE)
        if not selected_movie:
            messagebox.showerror("Error", "Please select a movie.")
            return

        try:
            con = connect_to_db()
            cursor = con.cursor()
            query = "DELETE FROM movies WHERE title = %s"
            cursor.execute(query, (selected_movie,))
            con.commit()
            con.close()
            messagebox.showinfo("Success", "Movie deleted successfully!")
            delete_window.destroy()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Database error: {err}")

    Button(delete_window, text="Delete", command=confirm_deletion, font=("Times New Roman", 12), bg="#a40000", fg="white").pack(pady=10)

# List movies
def list_movies():
    movies = fetch_movies()
    if not movies:
        messagebox.showerror("Error", "No movies to display.")
        return

    list_window = Toplevel(root)
    list_window.title("Movies")
    list_window.geometry("600x400")

    Label(list_window, text="Movies List", font=("Times New Roman", 16, "bold")).pack(pady=10)
    listbox = Listbox(list_window, font=("Times New Roman", 12), height=20, width=50)
    for movie in movies:
        listbox.insert(END, f"{movie[0]} - {movie[1]} min - {movie[2]}")
    listbox.pack(pady=10)

# Update movie details
def update_movie():
    movies = fetch_movies()
    if not movies:
        messagebox.showerror("Error", "No movies available for updating.")
        return

    update_window = Toplevel(root)
    update_window.title("Update Movie")
    update_window.geometry("400x600")

    Label(update_window, text="Select a movie to update:", font=("Times New Roman", 12)).pack(pady=10)
    movie_listbox = Listbox(update_window, font=("Times New Roman", 12), height=10)
    for movie in movies:
        movie_listbox.insert(END, movie[0])
    movie_listbox.pack(pady=10)

    def load_movie_details():
        selected_movie = movie_listbox.get(ACTIVE)
        if not selected_movie:
            messagebox.showerror("Error", "Please select a movie.")
            return

        movie_details = fetch_movie_details(selected_movie)
        if not movie_details:
            messagebox.showerror("Error", "Could not fetch movie details.")
            return

        entry_title.delete(0, END)
        entry_title.insert(0, movie_details[0])
        entry_genre.delete(0, END)
        entry_genre.insert(0, movie_details[1])
        entry_duration.delete(0, END)
        entry_duration.insert(0, movie_details[2])
        entry_release_date.delete(0, END)
        entry_release_date.insert(0, movie_details[6])

    def save_updated_movie():
        title = entry_title.get()
        genre = entry_genre.get()
        duration = entry_duration.get()
        release_date = entry_release_date.get()

        if not title or not genre or not duration or not release_date:
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            con = connect_to_db()
            cursor = con.cursor()
            query = """
                UPDATE movies
                SET title = %s, genre = %s, duration = %s, release_date = %s
                WHERE title = %s
            """
            cursor.execute(query, (title, genre, duration, release_date, movie_listbox.get(ACTIVE)))
            con.commit()
            con.close()
            messagebox.showinfo("Success", "Movie updated successfully!")
            update_window.destroy()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Database error: {err}")

    entry_title = Entry(update_window, font=("Times New Roman", 12))
    entry_genre = Entry(update_window, font=("Times New Roman", 12))
    entry_duration = Entry(update_window, font=("Times New Roman", 12))
    entry_release_date = Entry(update_window, font=("Times New Roman", 12))

    Button(update_window, text="Load Details", command=load_movie_details, font=("Times New Roman", 12)).pack(pady=10)
    Label(update_window, text="Title:", font=("Times New Roman", 12)).pack()
    entry_title.pack()
    Label(update_window, text="Genre:", font=("Times New Roman", 12)).pack()
    entry_genre.pack()
    Label(update_window, text="Duration:", font=("Times New Roman", 12)).pack()
    entry_duration.pack()
    Label(update_window, text="Release Date:", font=("Times New Roman", 12)).pack()
    entry_release_date.pack()
    Button(update_window, text="Save", command=save_updated_movie, font=("Times New Roman", 12), bg="orange", fg="white").pack(pady=10)

# Admin panel
def admin_panel():
    admin_window = Toplevel(root)
    admin_window.title("Admin Panel")
    admin_window.geometry("600x400")

    Label(admin_window, text="Admin Panel", font=("Times New Roman", 16, "bold")).pack(pady=20)

    Button(admin_window, text="Add Movie", command=add_movie, font=("Times New Roman", 14), bg="#458b00", fg="white").pack(pady=10)
    Button(admin_window, text="Delete Movie", command=delete_movie, font=("Times New Roman", 14), bg="#a40000", fg="white").pack(pady=10)
    Button(admin_window, text="Update Movie", command=update_movie, font=("Times New Roman", 14), bg="orange", fg="white").pack(pady=10)
    Button(admin_window, text="List Movies", command=list_movies, font=("Times New Roman", 14), bg="#191970", fg="white").pack(pady=10)


# Admin login
def admin_login():
    admin_password = entry_admin_password.get()

    # Admin password check 
    if admin_password == "1":  
        messagebox.showinfo("Admin Login", "Welcome Admin!")
        admin_login_window_instance.destroy() 
        admin_panel()  
    else:
        messagebox.showerror("Error", "Invalid admin password.")

# Admin login window
def admin_login_window():
    global entry_admin_password, admin_login_window_instance
    admin_login_window_instance = Toplevel(root)  # Create the window instance
    admin_login_window_instance.title("Admin Login")
    admin_login_window_instance.geometry("400x250")

    Label(admin_login_window_instance, text="Admin Login", font=("Times New Roman", 16, "bold")).pack(pady=20)
    Label(admin_login_window_instance, text="Password:", font=("Times New Roman", 14)).pack(pady=10)

    entry_admin_password = Entry(admin_login_window_instance, show="*", font=("Times New Roman", 14))
    entry_admin_password.pack(pady=10)

    Button(admin_login_window_instance, text="Log In", command=admin_login, font=("Times New Roman", 14), bg="#6f7a11", fg="white").pack(pady=20)

# Registration form
def register_user():
    username = reg_entry_username.get()
    password = reg_entry_password.get()
    email = reg_entry_email.get()

    if not username or not password or not email:
        messagebox.showerror("Error", "All fields are required!")
        return

    try:
        con = connect_to_db()
        cursor = con.cursor()

        check_query = "SELECT * FROM users WHERE email=%s"
        cursor.execute(check_query, (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            messagebox.showerror("Error", "This email is already registered. Please use a different email.")
            return

        query = "INSERT INTO users (user_name, password, email) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, password, email))
        con.commit()
        con.close()
        messagebox.showinfo("Success", "Registration successful!")
        reg_window.destroy()
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Database error: {err}")

# Register window
def register():
    global reg_window, reg_entry_username, reg_entry_password, reg_entry_email
    reg_window = Toplevel(root)
    reg_window.title("Register")
    reg_window.geometry("400x300")

    Label(reg_window, text="Username:", font=("Times New Roman", 14)).place(x=50, y=50)
    reg_entry_username = Entry(reg_window, font=("Times New Roman", 14))
    reg_entry_username.place(x=150, y=50, width=200)

    Label(reg_window, text="Password:", font=("Times New Roman", 14)).place(x=50, y=100)
    reg_entry_password = Entry(reg_window, show="*", font=("Times New Roman", 14))
    reg_entry_password.place(x=150, y=100, width=200)

    Label(reg_window, text="Email:", font=("Times New Roman", 14)).place(x=50, y=150)
    reg_entry_email = Entry(reg_window, font=("Times New Roman", 14))
    reg_entry_email.place(x=150, y=150, width=200)

    Button(reg_window, text="Sign Up", command=register_user, font=("Times New Roman", 14), bg="#4f94cd", fg="white").place(x=150, y=200, width=100)

# Main window (Login)
root = Tk()
root.title("Welcome Screen")
root.geometry("800x600")

try:
    background_image = Image.open(r"C:\\Users\\dilar\\OneDrive\\Masaüstü\\background.jpeg")
    background_image = background_image.resize((800, 600))
    bg = ImageTk.PhotoImage(background_image)
    bg_label = Label(root, image=bg)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
except FileNotFoundError:
    messagebox.showerror("Error", "Background image file not found. Please ensure the path is correct.")
    
frame = Frame(root, bg="black")
frame.place(x=375, y=150, width=400, height=300)

Label(frame, text="Username:", font=("Times New Roman", 16), bg="black", fg="white").place(x=20, y=50)
entry_username = Entry(frame, font=("Times New Roman", 14))
entry_username.place(x=150, y=50, width=200)

Label(frame, text="Password:", font=("Times New Roman", 16), bg="black", fg="white").place(x=20, y=100)
entry_password = Entry(frame, show="*", font=("Times New Roman", 14))
entry_password.place(x=150, y=100, width=200)

Button(frame, text="Log In", command=user_login, font=("Times New Roman", 14), bg="#a38c3d", fg="white").place(x=50, y=200, width=120)
Button(frame, text="Sign Up", command=register, font=("Times New Roman", 14), bg="#654321", fg="white").place(x=200, y=200, width=120)

# Admin login button
Button(frame, text="Admin Login", command=admin_login_window, font=("Times New Roman", 14), bg="#6f7a11", fg="white").place(x=125, y=250, width=120)

root.mainloop()