"""
Example usage of the new create_events function.
This demonstrates how to create multiple events for a single feature efficiently.
"""

from model.database import create_events, get_all_events_with_details


def example_login_workflow():
    """Example: Create a complete login workflow with multiple events."""
    
    # Define the login workflow events
    login_events = [
        {
            "operation_name": "input_text",
            "step_number": 1,
            "url": "https://bishnoishaadi.com/login",
            "html_component": "input[id='email']",
            "input_text": "HARSHBSHNOI@GMAIL.COM"
        },
        {
            "operation_name": "input_text",
            "step_number": 2,
            "url": "https://bishnoishaadi.com/login",
            "html_component": "input[id='password']",
            "input_text": "123456"
        },
        {
            "operation_name": "click",
            "step_number": 3,
            "url": "https://bishnoishaadi.com/login",
            "html_component": "button[type='submit']",
            "input_text": None
        }
    ]
    
    # Create all events for the login feature
    print("Creating login workflow events...")
    event_ids = create_events("Bishnoi Shaadi Login", login_events)
    
    print(f"\nCreated {len(event_ids)} events with IDs: {event_ids}")
    
    # Display all events in the database
    print("\nAll events in database:")
    events = get_all_events_with_details()
    for event in events:
        print(f"  - {event['step_number']}. {event['feature']}: {event['operation']} - {event['input_text'] or 'No input'}")


def example_registration_workflow():
    """Example: Create a registration workflow with multiple events."""
    
    # Define the registration workflow events
    registration_events = [
        {
            "operation_name": "input_text",
            "step_number": 1,
            "url": "https://example.com/register",
            "html_component": "input[name='firstName']",
            "input_text": "John"
        },
        {
            "operation_name": "input_text",
            "step_number": 2,
            "url": "https://example.com/register",
            "html_component": "input[name='lastName']",
            "input_text": "Doe"
        },
        {
            "operation_name": "input_text",
            "step_number": 3,
            "url": "https://example.com/register",
            "html_component": "input[name='email']",
            "input_text": "john.doe@example.com"
        },
        {
            "operation_name": "click",
            "step_number": 4,
            "url": "https://example.com/register",
            "html_component": "button[type='submit']",
            "input_text": None
        }
    ]
    
    # Create all events for the registration feature
    print("Creating registration workflow events...")
    event_ids = create_events("User Registration", registration_events)
    
    print(f"\nCreated {len(event_ids)} events with IDs: {event_ids}")


if __name__ == "__main__":
    print("=== Example: Using create_events function ===\n")
    
    # Run the login workflow example
    example_login_workflow()
    
    print("\n" + "="*50 + "\n")
    
    # Run the registration workflow example
    example_registration_workflow()
    
    print("\n=== All events in database ===")
    events = get_all_events_with_details()
    print(f"Total events: {len(events)}")
    for event in events:
        print(f"  - {event['step_number']}. {event['feature']}: {event['operation']} - {event['input_text'] or 'No input'}")
