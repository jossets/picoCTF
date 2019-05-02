"""Module for interacting with bundles."""

from voluptuous import Required, Schema

import api.db
from api.common import check, validate

bundle_schema = Schema({
    Required("name"):
    check(("The bundle name must be a string.", [str])),
    Required("author"):
    check(("The bundle author must be a string.", [str])),
    Required("categories"):
    check(("The bundle categories must be a list.", [list])),
    Required("problems"):
    check(("The bundle problems must be a list.", [list])),
    Required("description"):
    check(("The bundle description must be a string.", [str])),
    "organization":
    check(("The bundle organization must be a string.", [str])),
    "dependencies":
    check(("The bundle dependencies must be a dict.", [dict])),
    "dependencies_enabled":
    check(("The dependencies enabled state must be a bool.",
           [lambda x: type(x) == bool])),
    "pkg_dependencies":
    check(("The package dependencies must be a list.",
           [lambda x: type(x) == list]))
})


def get_bundle(bid):
    """
    Return the bundle dict corresponding to the given bid.

    Args:
        bid: bundle ID

    Returns:
        The associated bundle dict, or None if not found

    """
    db = api.db.get_conn()
    return db.bundles.find_one({"bid": bid}, {'_id': 0})


def get_all_bundles():
    """Get all bundles."""
    db = api.db.get_conn()
    return list(db.bundles.find({}, {"_id": 0}))


def upsert_bundle(bundle):
    """
    Add or update a bundle.

    Args:
        bundle: bundle dict

    Returns:
        The created/updated bundle ID.

    """
    db = api.db.get_conn()

    # Validate the bundle object
    # @TODO validate this at the routing level instead
    validate(bundle_schema, bundle)

    bid = api.common.hash("{}-{}".format(bundle["name"], bundle["author"]))

    # If the bundle already exists, update it instead
    existing = db.bundles.find_one({'bid': bid}, {'_id': 0})
    if existing is not None:
        db.bundles.find_one_and_update(
            {'bid': bid},
            {'$set': bundle}
        )
        return bid

    bundle["bid"] = bid
    bundle["dependencies_enabled"] = False

    db.bundles.insert(bundle)
    return bid


def set_bundle_dependencies_enabled(bid, enabled):
    """
    Set a bundle's dependencies_enabled field.

    This will affect the unlocked problems.

    Args:
        bid: the bundle id
        enabled: whether to enable the bundle's dependencies

    Returns:
        The bid of the updated bundle, or None if it could not be found.

    """
    db = api.db.get_conn()
    success = db.bundles.find_one_and_update(
        {'bid': bid}, {'$set': {
            'dependencies_enabled': enabled
        }})
    if not success:
        return None
    else:
        api.cache.clear()
        return bid
