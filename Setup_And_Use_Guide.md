# Setup

## Reset

1. Deactivate venv if activated with `deactivate`
2. Delete venv by deleting venv folder

## First time

1. Pull from git
2. Create virtual environment
    1. (Not sure if important) make sure you are running a newer version of python. 
        On the whitemachine, do this by running `conda activate anac`
    2. Navigate to top level of directory (anac-anl-2022-analysis)
    3. run `python -m venv venv`
3. Install modules with pip
    1. Start venv virtual environment by running 
        - `& ./venv/Scripts/activate` on Windows
        - `. ./venv/bin/activate` on Linux
    2. Run `pip install -r requirements.txt`
    3. Run `pip install -U kaleido` (I believe this is only needed to run create_profile.py)
4. Replace installed geniusweb modules with our version
    1. Copy the 2 folders inside geniusweb_module. Replace the versions in the virtual environment with these.
        - `venv/Lib/site-packages/` for Windows
        - `venv/lib/python3.10/site-packages/` for Linux (Probably replace python3.10 with your python version)
5. Create domains
    1. There are two ways to create the domains:
        - To recreate the domains, run `python utils/create_profile.py`.
          You may comment or uncomment lines in the "main" function to generate only some of the domains, 
          but don't uncomment the np.random.seed() lines
        - To use existing domains, unzip domains.zip. Be sure that the directory structure 
          looks like domains/basic/domain00/domain00.json, with no additional folders
6. You can now edit and run run_tournament.py `python run_tournament.py`

## New pull from github

- If no change was made to the modules, you can safely pull.
- If changes were made to the modules, you may pull and repeat step 4. 
- If changes were made to domains, you may pull and repeat step 5.

## Each time you start a new session

1. Navigate to top level of directory (anac-anl-2022-analysis)
2. Start venv virtual environment by running 
    - `& ./venv/Scripts/activate` on Windows
    - `. ./venv/bin/activate` on Linux
3. You can now edit and run run_tournament.py `python run_tournament.py`