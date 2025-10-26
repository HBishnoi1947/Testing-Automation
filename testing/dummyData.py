from model.database import create_event, get_all_events_with_details


def push_data_to_sqlite() -> None:
	"""Push Bishnoi Shaadi login test data to SQLite database using new schema."""
	# Create Bishnoi Shaadi login test events directly
	create_event("Bishnoi Shaadi Login", "input_text", 1, "https://bishnoishaadi.com/login", "input[id='email']", "HARSHBSHNOI@GMAIL.COM")
	create_event("Bishnoi Shaadi Login", "input_text", 2, "https://bishnoishaadi.com/login", "input[id='password']", "123456")
	create_event("Bishnoi Shaadi Login", "click", 3, "https://bishnoishaadi.com/login", "button[type='submit']", None)
	
	print("Pushed 3 Bishnoi Shaadi login test events to SQLite database")
	print("Events:")
	print("1. Enter email: HARSHBSHNOI@GMAIL.COM")
	print("2. Enter password: 123456")
	print("3. Click Sign In button")
	
	# Display the created events
	events = get_all_events_with_details()
	print(f"\nCreated {len(events)} events in database:")
	for event in events:
		print(f"  - {event['step_number']}. {event['feature']}: {event['operation']} - {event['input_text'] or 'No input'}")


if __name__ == "__main__":
	
	print("\n=== SQLite Version ===")
	# Run SQLite version
	push_data_to_sqlite()


