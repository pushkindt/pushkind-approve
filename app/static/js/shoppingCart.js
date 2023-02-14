function productOptionsToJson(form) {
    let formData = {};
    form.find('select').each(function () {
        let selected = $(this).find(':selected');
        let name = $(this).data('name');
        if (!selected.attr('disabled')) {
            formData[name] = selected.val();
        }
    });
    return formData;
}

function SetInCartText(shoppingCart) {
    let numItems = shoppingCart.length;
    if (numItems > 0) {
        let totalPrice = shoppingCart.reduce((a, b) => a + (b["price"] || 0) * (b["quantity"] || 0), 0);
        $("#inCartItems").text(numItems + " позиции на сумму " + totalPrice.toFixed(2));
    }
    else
        $("#inCartItems").text("");
}

function UpdateCartItem(item) {
    let cartItem = $('div.row[data-id="' + item["id"] + '"]');
    let input = $("#input-addon" + item["id"]);
    let text = $("#text-addon" + item["id"]);
    if (input) {
        input.val(item["quantity"]);
        input.addClass("border-success");
    }
    if (text)
        text.val(item["text"]);
    let options = Object.keys(item['options']);
    options.forEach((option) => {
        let select = cartItem.find('select[data-name="' + option + '"]');
        select.val(item['options'][option]).change()
    });
}

function UpdateCartItems(shoppingCart) {
    if (!shoppingCart) {
        shoppingCart = [];
        sessionStorage.setItem("shoppingCart", JSON.stringify(shoppingCart));
    } else {
        try {
            shoppingCart = JSON.parse(shoppingCart);
            shoppingCart.forEach(UpdateCartItem);
        } catch (e) {
            console.log(e);
            shoppingCart = [];
            sessionStorage.setItem("shoppingCart", JSON.stringify(shoppingCart));
        }
    }
    return shoppingCart;
}

function AddToCart(form, shoppingCart) {
    form.removeData("timer");
    let itemId = Number(form.data("id"));
    let itemName = form.data("name");
    let itemVendor = form.data("vendor");
    let itemImage = form.data("image");
    let itemSku = form.data("sku");
    let itemPrice = Number(form.data("price"));
    let input = form.find("input.addToCart");
    let itemQuantity = Number(input.val());
    let itemText = form.find("textarea.addToCart").val();
    let itemMeasurement = form.data("measurement");
    let itemOptions = productOptionsToJson(form);
    if (itemQuantity > 0) {
        let cartItem = shoppingCart.find((obj) => {
            return obj["id"] === itemId;
        });
        if (!cartItem) {
            cartItem = {
                id: itemId,
                name: itemName,
                sku: itemSku,
                price: itemPrice,
                vendor: itemVendor,
                image: itemImage,
                measurement: itemMeasurement,
            };
            shoppingCart.push(cartItem);
        }
        if (itemText)
            cartItem["text"] = itemText;
        if (itemOptions)
            cartItem["options"] = itemOptions;
        cartItem["quantity"] = itemQuantity;
        input.addClass("border-success");
    } else {
        shoppingCart = shoppingCart.filter((obj) => {
            return obj["id"] !== itemId;
        });
        input.removeClass("border-success");
    }
    sessionStorage.setItem("shoppingCart", JSON.stringify(shoppingCart));
    SetInCartText(shoppingCart);
}