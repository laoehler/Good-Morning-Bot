        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    message = "Good morning. Here is your schedule for today. "

    if not events:
        message += "You have no events today."
        print(message)
        speak_to_file(message)
        return

    for event in events:
        start_raw = event['start'].get('dateTime', event['start'].get('date'))
        title = event.get('summary', 'No Title')

        if 'T' in start_raw:
            dt = datetime.datetime.fromisoformat(start_raw.replace('Z', '+00:00')).astimezone()
            time_str = dt.strftime('%I:%M %p')
            message += f"At {time_str}, {title}. "
        else:
            message += f"All day: {title}. "

    print(message)
    speak_to_file(message)
    play_audio(OUTPUT_FILE)

if __name__ == '__main__':
    main()