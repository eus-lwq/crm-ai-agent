# Test Sentences for CRM Agent

## 📧 Email Sending Tests
*(Note: These require email tools to be added to the chat agent)*

### Simple Email
- "Send an email to john.doe@example.com with subject 'Follow-up Meeting' and body 'Let's schedule a follow-up meeting next week.'"
- "Email sarah@company.com about the proposal we discussed yesterday"
- "Send a message to contact@client.com with subject 'Project Update'"

### Email with Details
- "Send an email to eustinalwq@gmail.com to schedule an event on Nov 12 2025 to chat about next step deals"
- "Email michael@techcorp.com with the subject 'Q4 Review' and mention our quarterly performance metrics"
- "Send an email to team@startup.io inviting them to our product demo next Friday"

### Email with Context
- "Send a follow-up email to the contact from DataFlow Systems about the API integration proposal"
- "Email the customer who inquired about our enterprise pricing last week"

---

## 📅 Calendar Event Tests
*(Note: These require calendar tools to be added to the chat agent)*

### Simple Event Creation
- "Add a meeting to my calendar for November 12, 2025 at 2 PM to chat about next step deals"
- "Create a calendar event for tomorrow at 3 PM titled 'Client Call with TechCorp'"
- "Schedule a meeting on Nov 15, 2025 at 10 AM for 1 hour"

### Event with Attendees
- "Schedule a meeting with eustinalwq@gmail.com on Nov 12 2025 at 2 PM to discuss next step deals"
- "Add a calendar event for next Friday at 2 PM with attendees john@example.com and sarah@example.com"
- "Create a team meeting on Monday at 9 AM with the engineering team"

### Event with Details
- "Add a calendar event titled 'Product Demo' on November 12, 2025 at 2 PM, location: Conference Room A, description: Demo our new features to potential clients"
- "Schedule a 1-hour meeting on Nov 12, 2025 at 2 PM with eustinalwq@gmail.com about next step deals, location: Virtual (Zoom)"
- "Create an event 'Board Meeting' for tomorrow at 10 AM, duration 2 hours, with location 'HQ Conference Room'"

### Combined Email + Calendar
- "Send an email to eustinalwq@gmail.com to schedule an event on Nov 12 2025 to chat about next step deals? Also add it to my google calendar"
- "Email john@example.com and create a calendar invite for our meeting next Tuesday at 3 PM"
- "Send an invitation email and add a calendar event for the product launch meeting on December 1st at 2 PM"

---

## 📊 Table Querying Tests
*(These should work with current BigQuery tools)*

### Discovery Queries
- "What tables are available in the database?"
- "Show me all the tables in the CRM dataset"
- "List all available tables"

### Schema Queries
- "What's the schema of the deals table?"
- "Show me the structure of the customers table"
- "What columns are in the interactions table?"

### Data Queries
- "Show me all customers from the last 30 days"
- "What are the top 10 deals by value?"
- "List all interactions with contact name containing 'John'"
- "Show me deals worth more than $50,000"
- "Find all customers from TechCorp Inc"
- "What's the total deal value for this month?"

### Summary Queries
- "Give me a summary of customer ID 12345"
- "Show me customer information for DataFlow Systems"
- "What's the customer summary for the company 'FounderHub'?"

### Complex Queries
- "Show me all deals with follow-up dates in November 2025"
- "List customers who have interactions with deal value over $75,000"
- "Find all email interactions from the last week"
- "Show me all calendar-related interactions from this month"

---

## 🔄 Multi-Step Tests
*(Combining multiple capabilities)*

### Query + Action
- "Find all customers with deals over $50k and send them an email about our new product"
- "Show me upcoming follow-up dates and create calendar reminders for them"
- "List all customers from TechCorp and schedule a meeting with them next week"

### Analysis + Communication
- "What's our total deal value this month? Send a summary email to the team"
- "Show me the top 5 deals and create calendar events for follow-ups"
- "Find customers with no recent interactions and send them a re-engagement email"

---

## 💡 Tips for Testing

1. **Start Simple**: Begin with basic queries like "What tables are available?" to verify the agent is working
2. **Test Edge Cases**: Try dates in different formats, partial company names, etc.
3. **Natural Language**: The agent should understand conversational requests
4. **Error Handling**: Test with invalid inputs to see how the agent handles errors
5. **Context**: Try follow-up questions that reference previous queries

---

## 🚀 Quick Test Sequence

1. **Discovery**: "What tables are available?"
2. **Schema**: "What's the structure of the deals table?"
3. **Query**: "Show me the top 5 deals by value"
4. **Summary**: "Give me a customer summary for FounderHub"
5. **Email** (if tools added): "Send an email to test@example.com"
6. **Calendar** (if tools added): "Add a meeting for tomorrow at 2 PM"

