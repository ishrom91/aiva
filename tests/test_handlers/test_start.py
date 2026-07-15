import pytest
from aiogram.types import Message, User
from aiogram.methods import SendMessage
from src.handlers.start import command_start_handler


@pytest.mark.asyncio
async def test_command_start_handler_new_user(mock_bot, mock_update):
    """Test the start command handler for a new user."""
    # Mock user
    user = User(id=123456789, is_bot=False, first_name="Test", last_name="User", username="testuser")
    
    # Mock message
    message = Message(
        message_id=1,
        date=1234567890,
        chat=MagicMock(),
        from_user=user
    )
    message.from_user = user
    
    # Call the handler
    await command_start_handler(message)
    
    # Check that the bot sent a message
    mock_bot.send_message.assert_called_once()
    
    # Verify the call arguments
    call_args = mock_bot.send_message.call_args
    assert call_args[0][0] == message.chat.id  # First argument should be chat_id
    assert "Привет" in call_args[1]["text"]  # Text should contain greeting