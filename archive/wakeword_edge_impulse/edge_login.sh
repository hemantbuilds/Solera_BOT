#!/usr/bin/expect

set timeout -1

# Run the edge-impulse-linux-runner
spawn edge-impulse-linux-runner

# Provide the email address
expect "What is your user name or e-mail address (edgeimpulse.com)?" {
    send "YOUR_EI_USERNAME\r"
}

# Provide the password
expect "What is your password?" {
    send "YOUR_EI_PASSWORD\r"
}

# Select the project by directly sending the project name
expect "From which project do you want to load the model?" {
    send "Hemant Kumar / wakeup-1\r"
}

# Select the microphone by directly sending the microphone name
expect "Select a microphone" {
    send "USB-Audio - UACDemoV1.0\r"
}

# Continue running
interact
