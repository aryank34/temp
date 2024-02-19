from datetime import datetime, timedelta


def get_next_week():
    # Get the current date and time
    current_date = datetime.now()

    # Calculate the number of days until the next Monday
    days_until_next_monday = 7 - current_date.weekday() if current_date.weekday() > 0 else 1

    # Add the number of days until the next Monday to the current date
    next_monday = current_date + timedelta(days=days_until_next_monday)

    # Get the date of the next Monday at midnight
    next_monday_midnight = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get the date of the next to next Monday at midnight
    next_to_next_monday_midnight = next_monday_midnight + timedelta(days=7)

    return next_monday_midnight, next_to_next_monday_midnight