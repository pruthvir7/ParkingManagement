from app import send_alert  # Import the existing send_alert function

def send_dummy_alert():
    # Dummy details for the alert
    phone_number = "+919741078794"  # Replace with your verified Twilio phone number
    actual_license_plate = "KA01AB1234"
    reserved_license_plate = "Unregistered"

    # Create a message for the alert
    message = (
        f"Alert! License plate mismatch detected.\n"
        f"Actual: {actual_license_plate}\n"
        f"Reserved: {reserved_license_plate}.\n"
        f"Please verify immediately!"
    )

    print("Sending dummy alert...")
    
    # Call the send_alert function
    send_alert(phone_number, message)
    
    print(f"Alert sent to {phone_number} with message: {message}")

if __name__ == "__main__":
    send_dummy_alert()
