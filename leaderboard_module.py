"""
Leaderboard Module for Telegram Quiz Bot

This standalone module handles quiz result tracking and leaderboard display.
It works independently with JSON storage for easy integration.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple

# File path for storing results
RESULTS_FILE = os.path.join("data", "leaderboard_results.json")

def load_results() -> List[Dict]:
    """Load quiz results from the JSON file"""
    if not os.path.exists(RESULTS_FILE):
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
        return []
    
    try:
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_results(results: List[Dict]) -> None:
    """Save quiz results to the JSON file"""
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def record_quiz_result(quiz_id: Union[int, str], 
                      user_id: int, 
                      user_name: str, 
                      score: float, 
                      correct_answers: int, 
                      total_questions: int,
                      start_time: datetime, 
                      end_time: datetime) -> None:
    """
    Record a quiz result
    
    Args:
        quiz_id: ID of the quiz
        user_id: User's Telegram ID
        user_name: User's Telegram name
        score: Final score (with negative marking applied if enabled)
        correct_answers: Number of correct answers
        total_questions: Total number of questions
        start_time: When the quiz started
        end_time: When the quiz ended
    """
    # Convert to string for JSON storage
    quiz_id = str(quiz_id)
    user_id = str(user_id)
    
    # Calculate completion time in seconds
    if isinstance(start_time, datetime) and isinstance(end_time, datetime):
        completion_time = (end_time - start_time).total_seconds()
    else:
        completion_time = 0
    
    # Load existing results
    results = load_results()
    
    # Create new result entry
    new_result = {
        "quiz_id": quiz_id,
        "user_id": user_id,
        "user_name": user_name,
        "score": score,
        "correct_answers": correct_answers,
        "total_questions": total_questions,
        "completion_time": completion_time,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add to results
    results.append(new_result)
    
    # Save results
    save_results(results)

def get_leaderboard(quiz_id: Optional[Union[int, str]] = None, limit: int = 15) -> List[Dict]:
    """
    Get the leaderboard for a specific quiz
    
    Args:
        quiz_id: ID of the quiz to get results for, or None for all quizzes
        limit: Maximum number of entries to return
        
    Returns:
        List of result entries, sorted by score and time
    """
    results = load_results()
    
    # Filter results by quiz_id if specified
    if quiz_id is not None:
        quiz_id = str(quiz_id)
        results = [r for r in results if r.get("quiz_id") == quiz_id]
    
    # Sort by score (descending) and completion time (ascending)
    sorted_results = sorted(
        results, 
        key=lambda x: (-x.get("score", 0), x.get("completion_time", float('inf')))
    )
    
    # Return top entries
    return sorted_results[:limit]

def format_time(seconds: float) -> str:
    """Format seconds into minutes and seconds"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"

def generate_leaderboard_message(quiz_id: Optional[Union[int, str]] = None, 
                                quiz_title: Optional[str] = None) -> str:
    """
    Generate a formatted leaderboard message
    
    Args:
        quiz_id: ID of the quiz to get results for, or None for all quizzes
        quiz_title: Optional title for the leaderboard
        
    Returns:
        Formatted leaderboard message string
    """
    leaderboard = get_leaderboard(quiz_id)
    
    if not leaderboard:
        return "📊 *Leaderboard*\n\nNo quiz results recorded yet!"
    
    # Use provided title or generate based on quiz_id
    if quiz_title:
        title = quiz_title
    elif quiz_id:
        title = f"Quiz {quiz_id}"
    else:
        title = "All Quizzes"
    
    # Create header
    message = f"📊 *Leaderboard: {title}* 📊\n\n"
    
    # Get sample entry to determine total questions
    sample_entry = leaderboard[0]
    total_questions = sample_entry.get("total_questions", 0)
    
    # Add ranking
    for i, entry in enumerate(leaderboard, 1):
        # Get entry details
        user_name = entry.get("user_name", "Unknown")
        score = entry.get("score", 0)
        correct_answers = entry.get("correct_answers", 0)
        completion_time = entry.get("completion_time", 0)
        
        # Format score based on whether it's a float or int
        if isinstance(score, float) and score.is_integer():
            score_str = f"{int(score)}"
        elif isinstance(score, float):
            score_str = f"{score:.1f}"
        else:
            score_str = str(score)
        
        # Medal for top 3
        medal = ""
        if i == 1:
            medal = "🥇 "
        elif i == 2:
            medal = "🥈 "
        elif i == 3:
            medal = "🥉 "
        
        # Add entry to message
        message += (
            f"{medal}*{i}. {user_name}*\n"
            f"   Score: {score_str}  ({correct_answers}/{total_questions} correct)\n"
            f"   Time: {format_time(completion_time)}\n\n"
        )
    
    # Add footer
    message += "Use /play to start a new quiz!"
    
    return message

# Command handler function for Telegram
async def show_leaderboard_command(update, context):
    """
    Handler function for the /leaderboard command in Telegram
    
    This function can be called from your Telegram bot to display the leaderboard.
    Example usage in your bot code:
    
    application.add_handler(CommandHandler("leaderboard", show_leaderboard_command))
    """
    command_args = context.args
    quiz_id = None  # Default to showing all quizzes
    
    # Check if an ID was specified
    if command_args and len(command_args) > 0:
        try:
            quiz_id = int(command_args[0])
        except ValueError:
            await update.message.reply_text("Invalid quiz ID. Please provide a valid number.")
            return
    
    # Generate and send the leaderboard
    leaderboard_message = generate_leaderboard_message(quiz_id)
    await update.message.reply_text(leaderboard_message, parse_mode='Markdown')
