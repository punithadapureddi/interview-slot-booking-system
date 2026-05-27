# Interview Slot Booking System

A beginner-friendly Flask web application that helps a college admin manage interview slots and allows students to register, browse slots, book interviews, and manage their bookings from a clean interface.

## Features

- Student registration and login
- Separate admin login
- Admin can add, view, and delete interview slots
- Students can browse and book available slots
- Prevents duplicate bookings for the same slot
- Students can cancel their bookings
- Search slots by company name
- Dashboards for both admin and students
- Responsive UI built with Bootstrap 5

## Project Structure

```text
interview-slot-booking-system/
├── app.py
├── requirements.txt
├── README.md
├── interview_booking.db
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── templates/
    ├── base.html
    ├── login.html
    ├── register.html
    ├── student_dashboard.html
    ├── view_slots.html
    ├── my_bookings.html
    ├── admin_dashboard.html
    ├── admin_slots.html
    ├── add_slot.html
    └── slot_bookings.html
