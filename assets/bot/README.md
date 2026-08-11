# Bot Assets

This directory contains bot-specific assets for the Aiva AI Bot.

## Files

- `welcome.png` - Welcome message image for new users
- `booking_ok.png` - Confirmation image for successful bookings
- `reminder.png` - Reminder notification image
- `winback.png` - Win-back campaign image

## How to Upload Images and Get file_id

To use these images in the bot, you need to upload them to Telegram and get their file_id:

1. Send the image file to your bot using the Telegram client
2. Use the following code to retrieve the file_id:

```python
from aiogram import Bot

bot = Bot(token="YOUR_BOT_TOKEN")

# If you sent the photo to your bot, you can get the file_id from the message
# For example, if you received a message with a photo:
# photo_id = message.photo[-1].file_id  # Gets the highest resolution

# Or you can send the photo directly and capture the returned message:
with open("path/to/your/image.png", "rb") as image:
    sent_message = await bot.send_photo(chat_id=your_chat_id, photo=image)
    photo_id = sent_message.photo[-1].file_id
    print(f"file_id: {photo_id}")
```

3. Add the file_ids to your .env file as part of the `BOT_ASSET_FILE_IDS` setting:

```
BOT_ASSET_FILE_IDS={"welcome":"<file_id_for_welcome>","booking_ok":"<file_id_for_booking_ok>","reminder":"<file_id_for_reminder>","winback":"<file_id_for_winback>"}
```

4. The bot will then use these file_ids to send the images without having to upload them each time.