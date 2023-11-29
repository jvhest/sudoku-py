from __future__ import annotations

import json
import os
from typing import Any

import requests
from bs4 import BeautifulSoup

URL = "https://www.nytimes.com/puzzles/sudoku/medium"
CFG_DIR = "/home/jvh/.local/share/sudoku"


def get_puzzle_page() -> bytes | None:
    response = requests.get(URL)
    return response.content if response.ok else None


def extract_puzzle_data(puzzle_page: bytes) -> dict[str, Any]:
    s = (
        BeautifulSoup(puzzle_page, "html.parser")
        .find("div", attrs={"class": "pz-game-screen"})
        .find("script")
        .text
    )
    dict_as_text = s[s.index("{") :]
    return eval(dict_as_text)


def format_puzzle(puzzle_list: list[int]) -> str:
    puzzle_str = ""
    for i in range(9):
        for j in range(9):
            puzzle_str += str(puzzle_list[(i * 9) + j])
        puzzle_str += "/"
    return puzzle_str[:-1]


def write_puzzle_json(puzzle: dict[str, Any]) -> None:
    filename = "nytimes-" + puzzle["date"] + "-sudoku.json"
    file_path = os.path.join(CFG_DIR, filename)
    with open(file_path, "w") as f:
        f.write(json.dumps(puzzle, indent=1))


def main() -> None:
    puzzle_page = get_puzzle_page()
    if puzzle_page:
        puzzle_data = extract_puzzle_data(puzzle_page)
        puzzle = {}
        puzzle["date"] = puzzle_data["easy"]["print_date"].replace("-", "")
        for p in ["easy", "medium", "hard"]:
            puzzle[p] = {}
            puzzle[p]["puzzle_id"] = puzzle_data[p]["puzzle_id"]
            puzzle[p]["puzzle"] = {}
            puzzle[p]["puzzle"]["original"] = format_puzzle(
                puzzle_data[p]["puzzle_data"]["puzzle"],
            )
        write_puzzle_json(puzzle)
    else:
        print("website 'www.nytimes.com' niet bereikbaar")


if __name__ == "__main__":
    main()
