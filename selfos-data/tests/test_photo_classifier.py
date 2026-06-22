import pytest
from scripts.photo_classifier import classify_photo


def test_classify_food():
    assert classify_photo("lunch.jpg") == "food"
    assert classify_photo("dinner_meal.png") == "food"


def test_classify_receipt():
    assert classify_photo("receipt_001.png") == "receipt"
    assert classify_photo("check_bill.jpg") == "receipt"


def test_classify_people():
    assert classify_photo("family_selfie.jpg") == "people"
    assert classify_photo("friends_portrait.png") == "people"


def test_classify_other():
    assert classify_photo("random_photo.jpg") == "other"
    assert classify_photo("screenshot.png") == "other"