# TL;DR
- 99% of the actual coding work is done by ChatGPT, however in order to properly implement I had to understand what each module does and how.
- This document does not use ChatGPT and is written by myself. The README.md, however, is 90% written by ChatGPT with my supervision.
- Spent around 9 hours in the project. 2/3 of the time spent is tackling newly found problems / bug fixes
- I would like to learn a lot more about Git and Frontend (incl. UX) in the future, as they gave me the most trouble. (Ofc, I still need to work a lot on other components as well)


# My background
- I have some experience vibe-coding in Python, however my coding skills is very limited.
- I also have some experience reading through the very basics of React, FastAPI.
- I have some experience in JS/HTML (beginner level), but that was almost 5 years ago so I forgot most of it.
- No experience whatsoever in Git, and UXDesign, as well as DB management

# Selecting the project:
I chose to go with the CliniQ assessment project because the required data structure and the workflow seemed much simpler to me.
I could imagine the actual user experience that would be required (or so I thought).

# My policy in tackling the problem:
- Limited experience and limited time meant I needed to create a working product fast, and learn later
- As such I relied a lot on ChatGPT for the actual coding, however a lot of decision making process was done by me.


# Designing the project:
While I'm not sure if it's the right approach, I chose to go with the following for tackling this problem:

## 1. Creating user stories for the MVP based on what's written in the pdf
   
### As a doctor

- Ability to login to the doctor page from the user page
- Ability to register / delete / update availabiltiy
- Ability to see the list of reservations
- Ability to set each reservation to completed or no-show

### As a user (non-login)
- Ability to see the calendar based on doctor's availability
- Ability to reserve / cancel a slot
- Ability to see reserved slots

I will touch upon this later, but this is missing A LOT of probabilities.

## 2. Selecting the tech / framework for the project

### Priorities:
- ease of use / complexity
- familiarity
- reliability (using frameworks that are common)

### Tech chosen and reason
- Backend: Python, FastAPI, SQLModel, Uvicorn (ChatGPT recommendations but I know what they are based on my previous experience)
- DB: SQLite (Able to run locally)
- Authentication for Doctor: HTTP Basic (I assumed it would be OK for this assignment)
- Frontend: HTML + a little bit of JS (ChatGPT recommended me Jinja but I was not familiar with it so I rejected)
- Tests: pytest + httpx (ChatGPT recommendation, but I also heard they are pretty common)


## 3. Creating the data model
Most of this part is done by ChatGPT, however as I mentioned in section 1, the required data model seemed simple so I had no problem approving what ChatGPT proposed to me.

## 4. Creating the backend API
I went onto creating some very basic backend APIs to make sure that they do what is required, and to confirm that the tech I used will match the criteria.
This part went smoothly as well, as I had very basic understanding of FastAPI.

## 5. Testing (via curl commands)
These went fairly smoothly (had some Python-specific errors but was able to quickly resolve by putting init py).
At this point I was pretty confident in what I was doing, and went onto frontend.

## 6. Creating frontend
This part was difficult.
I let ChatGPT do all the work in creating basic frontend, but compared to other python modules this was very difficult to read.
(Thinking back, I should have used some kind of GUI editor instead of VSCode)

I opened up the webpage after launching the server. It looked barebones but functional.
I went onto creating pytest scenarios.

## 7. Running pytest and polishing (where I spent the rest of the time...)

At this point, about 3 hours had passed.
I thought I was about 80% complete but I was very wrong.

While designing the pytests, initially ChatGPT recoommended to me 1-2 happy path scenarios only and they passed successfully.
However, looking back at the frontend UI, I realized I had missed a lot of possible user scenarios and did not think thoroughly about the user experience.

I will touch cover the details in the next section.

#  The problems I faced during polishing

As there are too many, it would be too long to describe in detail how I solved each of the problems, so here is a short summary:

- Timezones: I did not understand how servers/frontend handle timezones, which caused errors in calculations. I had to set everything to UTC then convert to local in frontend.
- Overlaps / Double-booking: I had to avoid overlapping availabilities or appointments.
- Time-awareness: In order to avoid patients from booking past slots, the UI had to be aware of the current time. Same applies for doctors and their availabilities.
- Overall user experience (especially for doctor): Originally the doctor would have to pick the exact minute they are available using a dial picker, which was very annoying. I changed it to a 30-min select, but I would say it's still bad.
- Slot calculations: After creating the frontend I realized that the booking has to be done in slots. I went with 30 minutes.
- Comments: I had comments in Japanese for most of the codes but then I realized what this assignment is for...
- Frontend testing: I realized later that the pytests do not cover frontend buttons (which was kind of obvious...), resulting in a last-minute fix.
- More testing and error handling: Most of the original pytests included happy paths only. I had to add some to prevent invalid actions on some of the core functions (such as Auth, for example)
- Git / GitHub: As it was my first time coding, this gave me the most trouble. I almost uploaded my whole project directionary including .env by not putting .gitignore in root. Thankfully I realized at the last minute.

# What I think I did well
I could talk about my shortcomings all day, but I would also like to note on what I think I did well.
- Using ChatGPT efficiently: as the context is limited I utilized the memory feature as well as kept reminding some of the critical concepts / codes when generating
- Not taking what ChatGPT says for face value: I know that it tends to hallucinate, so oftentimes I intentionally chose to ignore what it says and confirm if my suspicions are right, before implementation
- Environment setup: Using uv, I think the time I spent in setting up my development environment was fairly short.
- Prioritization: I went with very minimal frontend as per the assignemnt. I also made a lot of decisions in NOT implementing stuff that is outside required scope.

# How I would do it in the future (if given the same assignment)

- Think thoroughly on the user experience. Create multiple user stories.
- Create a mock UI first to make sure there the user stories are sufficient.
- Use a proper HTML editor that supports GUI preview
- Find and implement a solution for testing frontend.
- Use GitHub during development to keep track of the changes

# Limitations & Additonal Features (if given more time)
Please refer to the bottom of README.md for this section.
