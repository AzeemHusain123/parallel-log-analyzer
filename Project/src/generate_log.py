import random
from datetime import datetime, timedelta

def generate_large_log_file(filename="huge_server.log", total_lines=1_000_000*1000):

    print(f"Generating {total_lines:,} log lines...")
    print(f"Saving to: {filename}\n")

    levels = ["INFO", "WARNING", "ERROR", "DEBUG", "SUCCESS"]
    messages = [
        "User authenticated successfully",
        "Disk usage high: {}%",
        "Database timeout occurred",
        "Connection reset by peer",
        "Processing API request",
        "Cache miss for key=user_{}",
        "Memory cleanup completed",
        "CPU usage normalized",
        "Unauthorized access attempt detected",
        "File not found: /var/data/file_{}.txt",
        "Service restarted due to failure",
        "New request from IP=192.168.{}.{}",
        "Scheduled backup completed",
        "API rate limit exceeded",
        "Queue size growing: {} items",
        "Email sent to user",
        "Data synchronization complete",
        "Job dispatcher started",
        "Session token generated",
        "Firewall rule applied"
    ]

    start_ts = datetime(2025, 1, 1, 0, 0, 0)

    with open(filename, "w", encoding="utf-8") as f:
        for i in range(total_lines):

            timestamp = start_ts + timedelta(seconds=i)
            ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            level = random.choice(levels)
            msg_template = random.choice(messages)

            # Count how many {} placeholders exist
            placeholder_count = msg_template.count("{}")

            if placeholder_count == 0:
                msg = msg_template
            else:
                values = tuple(random.randint(10, 9999) for _ in range(placeholder_count))
                msg = msg_template.format(*values)

            line = f"{ts_str} {level} {msg}\n"
            f.write(line)

            if i % 100000 == 0 and i > 0:
                print(f"Written {i:,} lines so far...")

    print("\nFinished!")
    print(f"Log file created at: {filename}")
    print(f"Total lines: {total_lines:,}")

# Run generator
generate_large_log_file()
