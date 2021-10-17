#!/usr/bin/env python3

import os
import argparse
import logging
import configparser
from datetime import datetime
import uuid
import sys
from tabulate import tabulate
import contextlib
import sqlite3
from lib import init_db, get_scalar, execute_statement, create_or_get_item, create_or_get_project, create_or_get_test, create_or_get_test_set, get_metric


def execute_statement_and_display_result(connection, command, headers, parameters=()):
    with contextlib.closing(connection.cursor()) as cursor:
        cursor.execute(command, parameters)
        records = cursor.fetchall()
        if len(records) > 0:
            print("\n" + tabulate(records, headers=headers) + "\n")
        else:
            print("No results.\n")


def projects_list(connection, args):
    query = "SELECT id, name, created_at FROM projects ORDER BY name;"
    headers = ["ID", "Name", "Created"]
    execute_statement_and_display_result(connection, query, headers)


def project_create(connection, args):
    execute_statement(connection, "INSERT OR IGNORE INTO projects (id, name) VALUES (?, ?);", (str(uuid.uuid4()), args.name))


def project_delete(connection, args):
    execute_statement(connection, "DELETE FROM projects WHERE name = ?", (args.name,))


def tests_list(connection, args):
    query = "SELECT tests.id, projects.name, tests.name, tests.created_at FROM tests INNER JOIN projects ON tests.project = projects.id WHERE projects.name = ? ORDER BY projects.name, tests.name"
    headers = ["ID", "Project", "Name", "Created"]
    execute_statement_and_display_result(connection, query, headers, (args.project,))


def test_rename(connection, args):
    query = "UPDATE tests SET name = ? WHERE name = ? AND project = (SELECT id FROM projects WHERE name = ?)"
    execute_statement(connection, query, (args.name2, args.name1, args.project))


def test_delete(connection, args):
    execute_statement(connection, "DELETE FROM tests WHERE name = ?", (args.name,))


def test_link(connection, args):
    with contextlib.closing(sqlite3.connect("pptam.db")) as connection:
        with connection:
            test_set_id = get_scalar(connection, "SELECT test_sets.id FROM test_sets INNER JOIN projects ON test_sets.project = projects.id WHERE test_sets.name = ? AND projects.name = ?", (args.set, args.project))
            if test_set_id is None:
                print("Cannot find test set.")
            else:
                test_id = get_scalar(connection, "SELECT tests.id FROM tests INNER JOIN projects ON tests.project = projects.id WHERE tests.name = ? AND projects.name = ?", (args.test, args.project))
                if test_id is None:
                    print("Cannot find test.")
                else:
                    execute_statement(connection, "INSERT OR IGNORE INTO test_set_tests (id, test_set, test) VALUES (?, ?, ?)", (str(uuid.uuid4()), test_set_id, test_id))


def profiles_list(connection, args):
    query = "SELECT operational_profiles.id, projects.name, operational_profiles.name FROM operational_profiles INNER JOIN projects ON operational_profiles.project = projects.id WHERE projects.name = ? ORDER BY projects.name, operational_profiles.name"
    headers = ["ID", "Project", "Name"]
    execute_statement_and_display_result(connection, query, headers, (args.project,))


def profile_rename(connection, args):
    query = f"UPDATE operational_profiles SET name = ? WHERE name = ? AND project = (SELECT id FROM projects WHERE name = ?)"
    execute_statement(connection, query, (args.name2, args.name1, args.project))

def profile_delete(connection, args):
    execute_statement(connection, "DELETE FROM operational_profiles WHERE name = ?", (args.name, ))


def sets_list(connection, args):
    query = "SELECT test_sets.id, projects.name, test_sets.name, count(test_set_tests.id) FROM test_sets LEFT OUTER JOIN test_set_tests ON test_sets.id = test_set_tests.test_set INNER JOIN projects ON test_sets.project = projects.id WHERE projects.name = ? GROUP BY test_sets.id, projects.name, test_sets.name ORDER BY test_sets.id, projects.name, test_sets.name"
    headers = ["ID", "Project", "Name", "Tests"]
    execute_statement_and_display_result(connection, query, headers, (args.project,))


def set_create(connection, args):
    project_id = get_scalar(connection, "SELECT id FROM projects WHERE name = ?", (args.project, ))
    if project_id is None:
        print("Cannot find project.")
    else:
        query = "INSERT INTO test_sets (id, project, name) VALUES (?, ?, ?)"
        execute_statement(connection, query, (str(uuid.uuid4()), project_id, args.name))

def set_rename(connection, args):
    query = "UPDATE test_sets SET name = ? WHERE name = ? AND project = (SELECT id FROM projects WHERE name = ?)"
    execute_statement(connection, query, (args.name2, args.name1, args.project))

def set_delete(connection, args):
    execute_statement(connection, "DELETE FROM test_sets WHERE name = ?", (args.name, ))

def set_show(connection, args):
    query = "SELECT tests.id, tests.name FROM tests INNER JOIN projects ON tests.project = projects.id INNER JOIN test_set_tests ON test_set_tests.test = tests.id INNER JOIN test_sets ON test_set_tests.test_set = test_sets.id WHERE projects.name = ? AND test_sets.name = ? ORDER BY tests.name"
    headers = ["ID", "Name"]
    execute_statement_and_display_result(connection, query, headers, (args.project, args.set))


def add_sample_operational_profile(connection, args):
    with contextlib.closing(sqlite3.connect("pptam.db")) as connection:
        with connection:
            project_id = get_scalar(connection, "SELECT id FROM projects WHERE name = ?", (args.project,))
            if project_id is None:
                print("Cannot find project.")
            else:
                id = str(uuid.uuid4())
                execute_statement(connection, "INSERT INTO operational_profiles (id, project, name) VALUES (?, ?, ?)", (id, project_id, "Operational profile"))

                if args.number == 1:
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 0, 3))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 1, 11))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 2, 6))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 3, 6))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 4, 6))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 5, 8))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 10, 2))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 11, 4))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 12, 2))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 13, 2))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 15, 4))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 16, 4))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 17, 8))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 18, 7))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 19, 7))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 20, 7))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 21, 7))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 22, 6))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 23, 5))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 24, 1))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 25, 4))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 26, 3))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 27, 3))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 28, 4))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 30, 10))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 35, 13))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 40, 21))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 42, 10))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 45, 20))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 50, 12))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 55, 19))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 60, 25))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 65, 28))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 70, 26))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 75, 18))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 80, 16))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 105, 1))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 85, 17))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 90, 15))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 95, 6))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 100, 1))

                if args.number == 2:
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 10, 0))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 11, 0))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 12, 0))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 13, 0))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 14, 0))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 15, 3))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 16, 11))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 17, 6))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 18, 6))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 19, 6))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 20, 8))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 25, 2))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 26, 4))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 27, 2))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 28, 2))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 30, 4))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 31, 4))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 32, 8))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 33, 7))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 34, 7))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 35, 7))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 36, 7))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 37, 6))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 38, 5))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 39, 1))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 40, 4))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 41, 3))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 42, 3))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 43, 4))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 45, 10))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 50, 13))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 55, 21))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 57, 10))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 60, 20))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 65, 12))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 70, 19))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 75, 25))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 80, 28))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 85, 26))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 90, 18))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 95, 16))
                    execute_statement(connection, "INSERT INTO operational_profile_observations (id, operational_profile, users, frequency) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), id, 100, 17))


if __name__ == "__main__":
    if not os.path.exists("pptam.db"):
        logging.debug(f"Creating database since pptam.db does not exist.")
        init_db()

    parser = argparse.ArgumentParser(description="Organize items stored in the database")
    parser.add_argument("--logging", help="Logging level from 1 (everything) to 5 (nothing)", type=int, choices=range(1, 6), default=1)

    subparsers = parser.add_subparsers(dest="command", required=True, help="One of the following commands:")
    subparser_projects = subparsers.add_parser("projects", help="Manage projects")
    subparser_projects_subparser = subparser_projects.add_subparsers(dest="action", required=True, help="One of the following actions:")
    subparser_projects_subparser_create = subparser_projects_subparser.add_parser("create", help="Create projects")
    subparser_projects_subparser_create.add_argument("name", help="The name of the project")
    subparser_projects_subparser_delete = subparser_projects_subparser.add_parser("delete", help="Delete projects")
    subparser_projects_subparser_delete.add_argument("name", help="The name of the project")
    subparser_projects_subparser_list = subparser_projects_subparser.add_parser("list", help="List projects")

    subparser_profiles = subparsers.add_parser("profiles", help="Manage operational profiles")
    subparser_profiles_subparser = subparser_profiles.add_subparsers(dest="action", required=True, help="One of the following actions:")
    subparser_profiles_subparser_rename = subparser_profiles_subparser.add_parser("rename", help="Rename operational profiles")
    subparser_profiles_subparser_rename.add_argument("project", help="The name of the project")
    subparser_profiles_subparser_rename.add_argument("name1", help="The name of the operational profile to rename")
    subparser_profiles_subparser_rename.add_argument("name2", help="The new name of the operational profile to rename")
    subparser_profiles_subparser_delete = subparser_profiles_subparser.add_parser("delete", help="Delete operational profiles")
    subparser_profiles_subparser_delete.add_argument("project", help="The name of the project")
    subparser_profiles_subparser_delete.add_argument("name", help="The name of the operational profile")
    subparser_profiles_subparser_list = subparser_profiles_subparser.add_parser("list", help="List operational profiles")
    subparser_profiles_subparser_list.add_argument("project", help="The name of the project")

    subparser_sets = subparsers.add_parser("sets", help="Manage test sets")
    subparser_sets_subparser = subparser_sets.add_subparsers(dest="action", required=True, help="One of the following actions:")
    subparser_sets_subparser_rename = subparser_sets_subparser.add_parser("rename", help="Rename test sets")
    subparser_sets_subparser_rename.add_argument("project", help="The name of the project")
    subparser_sets_subparser_rename.add_argument("name1", help="The name of the test set to rename")
    subparser_sets_subparser_rename.add_argument("name2", help="The new name of the test set to rename")
    subparser_sets_subparser_delete = subparser_sets_subparser.add_parser("delete", help="Delete test sets")
    subparser_sets_subparser_delete.add_argument("project", help="The name of the project")
    subparser_sets_subparser_delete.add_argument("name", help="The name of the test set")
    subparser_sets_subparser_list = subparser_sets_subparser.add_parser("list", help="List test sets")
    subparser_sets_subparser_list.add_argument("project", help="The name of the project")
    subparser_sets_subparser_create = subparser_sets_subparser.add_parser("create", help="Create test sets")
    subparser_sets_subparser_create.add_argument("project", help="The name of the project")
    subparser_sets_subparser_create.add_argument("name", help="The name of the test set")
    subparser_sets_subparser_show = subparser_sets_subparser.add_parser("show", help="Show tests within a test set")
    subparser_sets_subparser_show.add_argument("project", help="The name of the project")
    subparser_sets_subparser_show.add_argument("set", help="The name of the test set")

    subparser_tests = subparsers.add_parser("tests", help="Manage tests")
    subparser_tests_subparser = subparser_tests.add_subparsers(dest="action", required=True, help="One of the following actions:")
    subparser_tests_subparser_rename = subparser_tests_subparser.add_parser("rename", help="Rename tests")
    subparser_tests_subparser_rename.add_argument("project", help="The name of the project")
    subparser_tests_subparser_rename.add_argument("name1", help="The name of the test to rename")
    subparser_tests_subparser_rename.add_argument("name2", help="The new name of the test to rename")
    subparser_tests_subparser_delete = subparser_tests_subparser.add_parser("delete", help="Delete tests")
    subparser_tests_subparser_delete.add_argument("project", help="The name of the project")
    subparser_tests_subparser_delete.add_argument("name", help="The name of the test")
    subparser_tests_subparser_list = subparser_tests_subparser.add_parser("list", help="List tests")
    subparser_tests_subparser_list.add_argument("project", help="The name of the project")
    subparser_tests_subparser_link = subparser_tests_subparser.add_parser("link", help="Link tests to test sets")
    subparser_tests_subparser_link.add_argument("project", help="The name of the project")
    subparser_tests_subparser_link.add_argument("test", help="The name of the test")
    subparser_tests_subparser_link.add_argument("set", help="The name of the test set")

    subparser_sample = subparsers.add_parser("sample", help="Manage sample data")
    subparser_sample_subparser = subparser_sample.add_subparsers(dest="action", required=True, help="One of the following actions:")
    subparser_sample_subparser_add = subparser_sample_subparser.add_parser("profile", help="Add sample operational profile")
    subparser_sample_subparser_add.add_argument("project", help="The name of the project")
    subparser_sample_subparser_add.add_argument("number", help="The number of the operational profile", type=int, choices=[1, 2])

    args = parser.parse_args()

    logging.basicConfig(format="%(message)s", level=args.logging * 10)

    switcher = {
        "projects_list": projects_list,
        "projects_create": project_create,
        "projects_delete": project_delete,
        "profiles_list": profiles_list,
        "profiles_rename": profile_rename,
        "profiles_delete": profile_delete,
        "sets_list": sets_list,
        "sets_rename": set_rename,
        "sets_delete": set_delete,
        "sets_create": set_create,
        "sets_show": set_show,
        "tests_list": tests_list,
        "tests_rename": test_rename,
        "tests_delete": test_delete,
        "tests_link": test_link,
        "sample_profile": add_sample_operational_profile,
    }

    with contextlib.closing(sqlite3.connect("pptam.db")) as connection:
        with connection:
            switcher.get(args.command + "_" + args.action)(connection, args)
