def lookForException(stats_queue):
    exceptions = []
    while not stats_queue.empty():
        item = stats_queue.get()
        if item['topic'] == 'Exception':
            exceptions.append(item['location'])
    if len(exceptions) > 0:
        raise Exception("An Exception occurred in " + ' & '.join(exceptions))
