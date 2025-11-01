# src/background_scheduler.py
"""
Background scheduler for automatic medication reminders and daily recaps.
Run this in a separate terminal: poetry run python src/background_scheduler.py
"""
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Fix import path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_all_medications, update_medication, get_settings
from src.smart_reminder import generate_smart_reminder
from src.recap_generator import generate_daily_recap
from src.text_to_speech import text_to_speech

# Directory for scheduled audio files
SCHEDULED_AUDIO_DIR = Path("scheduled_audio")
SCHEDULED_AUDIO_DIR.mkdir(exist_ok=True)


def check_medication_times():
    """Check if any medications are due and generate reminders"""
    try:
        medications = get_all_medications()
        now = datetime.now()
        current_time = now.strftime("%I:%M %p")
        today_name = now.strftime("%A")

        for med in medications:
            med_id = str(med.get('_id') or med.get('id'))
            med_time = med.get('time_to_take', '')

            # Check if it's time for this medication
            if med_time != current_time:
                continue

            # Check schedule type
            stype = med.get('schedule_type')
            should_remind = False

            if stype == 'Daily':
                should_remind = True
            elif stype == 'Weekly':
                if today_name in med.get('days_of_week', []):
                    should_remind = True
            elif stype == 'One-Time':
                sdate = med.get('specific_date')
                if isinstance(sdate, datetime):
                    if sdate.date() == now.date():
                        should_remind = True

            if not should_remind:
                continue

            # Check if already reminded recently (within last hour)
            last_reminded = med.get('last_reminded')
            if last_reminded:
                if isinstance(last_reminded, str):
                    last_reminded = datetime.fromisoformat(last_reminded)
                if now - last_reminded < timedelta(hours=1):
                    continue  # Already reminded

            # Generate reminder
            print(f"⏰ TIME FOR MEDICATION: {med.get('name')} at {med_time}")
            audio_path = generate_smart_reminder(med)

            if audio_path:
                # Save to scheduled directory with timestamp
                scheduled_filename = f"med_{med_id}_{now.strftime('%Y%m%d_%H%M%S')}.mp3"
                scheduled_path = SCHEDULED_AUDIO_DIR / scheduled_filename

                # Copy audio to scheduled directory
                import shutil
                shutil.copy(str(audio_path), str(scheduled_path))

                print(f"✅ Medication reminder saved: {scheduled_path}")
                print(f"   Patient View will auto-play this reminder")

                # Update last_reminded timestamp
                update_medication(med_id, {"last_reminded": now})

                # Clean up original temp file
                try:
                    os.remove(audio_path)
                except:
                    pass

    except Exception as e:
        print(f"❌ Error checking medications: {e}")


def check_daily_recap():
    """Check if it's time for daily recap"""
    try:
        settings = get_settings()

        if not settings.get('daily_recap_enabled', True):
            return

        recap_time = settings.get('daily_recap_time', '19:00')  # Default 7 PM
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        if current_time != recap_time:
            return

        # Check if recap already generated today
        recap_marker = SCHEDULED_AUDIO_DIR / f"recap_{now.strftime('%Y%m%d')}.marker"
        if recap_marker.exists():
            return  # Already done today

        print(f"🌅 TIME FOR DAILY RECAP: {recap_time}")

        # Generate recap
        recap_script = generate_daily_recap()
        audio_path = text_to_speech(recap_script, output_filename="temp_scheduled_recap.mp3")

        if audio_path:
            # Save to scheduled directory
            scheduled_filename = f"recap_{now.strftime('%Y%m%d_%H%M%S')}.mp3"
            scheduled_path = SCHEDULED_AUDIO_DIR / scheduled_filename

            import shutil
            shutil.copy(str(audio_path), str(scheduled_path))

            print(f"✅ Daily recap saved: {scheduled_path}")
            print(f"   Patient View will auto-play this recap")

            # Create marker file
            recap_marker.touch()

            # Clean up temp file
            try:
                os.remove(audio_path)
            except:
                pass

    except Exception as e:
        print(f"❌ Error checking daily recap: {e}")


def main():
    """Main scheduler loop"""
    print("=" * 50)
    print("🤖 RememberMe Background Scheduler")
    print("=" * 50)
    print("Monitoring for:")
    print("  - Medication times (checks every minute)")
    print("  - Daily recap schedule")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print("=" * 50)

    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"⏱️  Checking... {current_time}", end="\r")

            # Check medications
            check_medication_times()

            # Check daily recap
            check_daily_recap()

            # Wait 60 seconds before next check
            time.sleep(60)

    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped")


if __name__ == "__main__":
    main()