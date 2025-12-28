from quart import Blueprint, jsonify

test_bp = Blueprint("test", __name__, url_prefix="/")


@test_bp.route("/")
async def test():
    return jsonify({"DEBUG": True}), 200
