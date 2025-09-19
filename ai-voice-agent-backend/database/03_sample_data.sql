-- Sample data for AI Voice Agent Tool
-- Insert sample agents and test data

-- Insert sample agents
INSERT INTO agents (
    name, 
    description, 
    initial_prompt, 
    emergency_prompt, 
    follow_up_prompts,
    voice_id,
    is_active
) VALUES 
(
    'Logistics Dispatch Agent',
    'Primary agent for routine driver check-ins and emergency handling',
    'Hi {driver_name}, this is Dispatch with a check call on load {load_number}. Can you give me an update on your status?',
    'I understand this is an emergency situation. Please stay calm and tell me what happened. Are you and anyone else safe? What is your current location?',
    '["Can you tell me your current location?", "What is your estimated time of arrival?", "Are there any delays or issues?", "Is your load secure?", "Do you need any assistance?"]',
    'sarah',
    true
),
(
    'Emergency Response Agent',
    'Specialized agent for emergency situations and crisis management',
    'This is an emergency response call. Please describe the situation clearly.',
    'I understand this is an emergency. Please confirm: Are you safe? Is anyone injured? What is your exact location? I am connecting you to a human dispatcher immediately.',
    '["Are you safe?", "Is anyone injured?", "What is your exact location?", "Is your load secure?", "Do you need medical assistance?"]',
    'michael',
    true
);

-- Insert sample users (these would normally be created through Supabase Auth)
-- Note: These are placeholder UUIDs - real users will be created through authentication
INSERT INTO users (id, email, role) VALUES 
(
    '00000000-0000-0000-0000-000000000001',
    'admin@example.com',
    'admin'
),
(
    '00000000-0000-0000-0000-000000000002',
    'user@example.com',
    'user'
);

-- Insert sample web calls
INSERT INTO calls (
    agent_id,
    driver_name,
    phone_number,
    load_number,
    status,
    web_call_url,
    join_url,
    transcript,
    structured_data
) VALUES 
(
    (SELECT id FROM agents WHERE name = 'Logistics Dispatch Agent' LIMIT 1),
    'Mike Johnson',
    '+15551234567',
    '7891-B',
    'completed',
    'http://localhost:3000/call/sample-call-1',
    'https://retell.ai/join/sample-call-1',
    'Hi Mike, this is Dispatch with a check call on load 7891-B. Can you give me an update on your status? I''m currently driving on I-10 near Indio, CA. I should be there tomorrow around 8:00 AM. No delays, everything is going smoothly.',
    '{"call_outcome": "In-Transit Update", "driver_status": "Driving", "current_location": "I-10 near Indio, CA", "eta": "Tomorrow, 8:00 AM", "delay_reason": "None"}'
),
(
    (SELECT id FROM agents WHERE name = 'Logistics Dispatch Agent' LIMIT 1),
    'Sarah Williams',
    '+15559876543',
    '4521-C',
    'completed',
    'http://localhost:3000/call/sample-call-2',
    'https://retell.ai/join/sample-call-2',
    'Hi Sarah, this is Dispatch with a check call on load 4521-C. Can you give me an update on your status? I just arrived at the destination. I''m at door 42 and waiting for the lumper to show up.',
    '{"call_outcome": "Arrival Confirmation", "driver_status": "Unloading", "current_location": "Destination", "unloading_status": "In Door 42", "pod_reminder_acknowledged": true}'
),
(
    (SELECT id FROM agents WHERE name = 'Emergency Response Agent' LIMIT 1),
    'John Davis',
    '+15555555555',
    '1234-A',
    'completed',
    'http://localhost:3000/call/sample-call-3',
    'https://retell.ai/join/sample-call-3',
    'I just had a blowout, I''m pulling over! Everyone is safe, no injuries. I''m on I-15 North at mile marker 123. The load is secure.',
    '{"call_outcome": "Emergency Escalation", "emergency_type": "Breakdown", "safety_status": "Driver confirmed everyone is safe", "injury_status": "No injuries reported", "emergency_location": "I-15 North, Mile Marker 123", "load_secure": true, "escalation_status": "Connected to Human Dispatcher"}'
);

-- Insert corresponding call results
INSERT INTO call_results (
    call_id,
    call_outcome,
    driver_status,
    current_location,
    eta,
    delay_reason,
    unloading_status,
    pod_reminder_acknowledged
) VALUES 
(
    (SELECT id FROM calls WHERE load_number = '7891-B' LIMIT 1),
    'In-Transit Update',
    'Driving',
    'I-10 near Indio, CA',
    'Tomorrow, 8:00 AM',
    'None',
    NULL,
    NULL
),
(
    (SELECT id FROM calls WHERE load_number = '4521-C' LIMIT 1),
    'Arrival Confirmation',
    'Unloading',
    'Destination',
    NULL,
    NULL,
    'In Door 42',
    true
);

INSERT INTO call_results (
    call_id,
    call_outcome,
    emergency_type,
    safety_status,
    injury_status,
    emergency_location,
    load_secure,
    escalation_status
) VALUES 
(
    (SELECT id FROM calls WHERE load_number = '1234-A' LIMIT 1),
    'Emergency Escalation',
    'Breakdown',
    'Driver confirmed everyone is safe',
    'No injuries reported',
    'I-15 North, Mile Marker 123',
    true,
    'Connected to Human Dispatcher'
);
