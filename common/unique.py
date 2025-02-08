def unique(target: list) -> list:
    if isinstance(target, list):
        print("Please enter list type variable")
        raise TypeError

    result = [target.pop(0)]
    for element in target:
        if element in result:
            continue
        result.append(element)
    return element
