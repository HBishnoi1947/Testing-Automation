from model import ActionSpec, OperationType, save_action_to_excel


def main() -> None:
	# Bishnoi Shaadi Login Test - 3 actions only
	
	# Action 1: Enter email
	a1 = ActionSpec(
		url="https://bishnoishaadi.com/login",  # Update with actual URL
		htmlComponent="input[id='email']",
		operationType=OperationType.INPUT_TEXT,
		Input="HARSHBSHNOI@GMAIL.COM",
	)
	save_action_to_excel(a1)
	
	# Action 2: Enter password
	a2 = ActionSpec(
		url="https://bishnoishaadi.com/login",  # Update with actual URL
		htmlComponent="input[id='password']",
		operationType=OperationType.INPUT_TEXT,
		Input="123456",
	)
	save_action_to_excel(a2)
	
	# Action 3: Click login button
	a3 = ActionSpec(
		url="https://bishnoishaadi.com/login",  # Update with actual URL
		htmlComponent="button[type='submit']",
		operationType=OperationType.CLICK,
	)
	save_action_to_excel(a3)

	print("Saved 3 Bishnoi Shaadi login test actions to actions.xlsx")
	print("Actions:")
	print("1. Enter email: HARSHBSHNOI@GMAIL.COM")
	print("2. Enter password: 123456")
	print("3. Click Sign In button")


if __name__ == "__main__":
	main()


