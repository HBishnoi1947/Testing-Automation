from model import ActionSpec, OperationType, save_action_to_excel


def main() -> None:
	# Create a few dummy actions
	a1 = ActionSpec(
		url="https://playwright.dev",
		htmlComponent="a:has-text('Get started')",
		operationType=OperationType.CLICK,
	)
	save_action_to_excel(a1)

	a2 = ActionSpec(
		url="https://example.com",
		htmlComponent="input[name='q']",
		operationType=OperationType.INPUT_TEXT,
		Input="hello world",
	)
	save_action_to_excel(a2)

	a3 = ActionSpec(
		url="https://example.com",
		htmlComponent="#footer",
		operationType=OperationType.SCROLL,
	)
	save_action_to_excel(a3)

	print("Saved 3 dummy actions to actions.xlsx (sorted by id)")


if __name__ == "__main__":
	main()


