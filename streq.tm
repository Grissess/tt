TuringMachine[
	State['START'],
	Tape['LMARK', Head['0'], '0', '1', '1', '0', 'SEP', '0', '0', '1', '1', '0', 'EMPTY', 'RMARK'],
	Transitions[
		Transition['START', '0', 'RIGHT', 'MARK', 'RIGHT_0'],
		Transition['START', '1', 'RIGHT', 'MARK', 'RIGHT_1'],
		Transition['RIGHT_0', '0', 'RIGHT', '0', 'RIGHT_0'],
		Transition['RIGHT_0', '1', 'RIGHT', '1', 'RIGHT_0'],
		Transition['RIGHT_0', 'SEP', 'RIGHT', 'SEP', 'SEEN_0'],
		Transition['SEEN_0', 'MARK', 'RIGHT', 'MARK', 'SEEN_0'],
		Transition['SEEN_0', '0', 'LEFT', 'MARK', 'RETURN'],
		Transition['RIGHT_1', '0', 'RIGHT', '0', 'RIGHT_1'],
		Transition['RIGHT_1', '1', 'RIGHT', '1', 'RIGHT_1'],
		Transition['RIGHT_1', 'SEP', 'RIGHT', 'SEP', 'SEEN_1'],
		Transition['SEEN_1', 'MARK', 'RIGHT', 'MARK', 'SEEN_1'],
		Transition['SEEN_1', '1', 'LEFT', 'MARK', 'RETURN'],
		Transition['RETURN', 'MARK', 'LEFT', 'MARK', 'RETURN'],
		Transition['RETURN', 'SEP', 'LEFT', 'SEP', 'RETURN_CHECK'],
		Transition['RETURN_CHECK', 'MARK', 'RIGHT', 'MARK', 'ACCEPT'],
		Transition['RETURN_CHECK', '0', 'LEFT', '0', 'RETURN_CHECK'],
		Transition['RETURN_CHECK', '1', 'LEFT', '1', 'RETURN_CHECK'],
		Transition['RETURN_CHECK', 'MARK', 'RIGHT', 'MARK', 'START']
	]
]
