from model import create_bishnoi_shaadi_login_test, get_all_events_with_details


def push_data_to_sqlite() -> None:
	"""Push Bishnoi Shaadi login test data to SQLite database using new schema."""
	# Create Bishnoi Shaadi login test using new schema
	create_bishnoi_shaadi_login_test()
	
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


