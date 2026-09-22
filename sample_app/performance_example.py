def find_duplicates(items):
    duplicates = []

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])

    return duplicates