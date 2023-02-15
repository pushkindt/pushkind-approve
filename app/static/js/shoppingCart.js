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

function UpdateProductQuantity(item) {
    let input = $("#product" + item["id"] + " input");
    if (input) {
        input.val(item["quantity"]);
        input.addClass("border-success");
    }
}

function SyncShoppingCart() {
    shoppingCart = sessionStorage.getItem("shoppingCart");
    if (!shoppingCart) {
        shoppingCart = [];
        sessionStorage.setItem("shoppingCart", JSON.stringify(shoppingCart));
    } else {
        try {
            shoppingCart = JSON.parse(shoppingCart);
            $(".productQuantity").val(null);
            $(".productQuantity").removeClass("border-success");
            shoppingCart.forEach(UpdateProductQuantity);
        } catch (e) {
            console.log(e);
            shoppingCart = [];
            sessionStorage.setItem("shoppingCart", JSON.stringify(shoppingCart));
        }
    }
    SetInCartText(shoppingCart);
    return shoppingCart;
}

function SyncProductModal(form, shoppingCart) {
    let productId = Number(form.data("id"));

    let cartItem = shoppingCart.find((obj) => {
        return obj["id"] === productId;
    });
    if (!cartItem)
        return;
    let quantityInput = form.find("input");
    quantityInput.val(cartItem["quantity"]);
    let textInput = form.find("textarea");
    textInput.val(cartItem["text"]);
    let options = Object.keys(cartItem['options']);
    options.forEach((option) => {
        let select = form.find('select[data-name="' + option + '"]');
        select.val(cartItem['options'][option]).change()
    });
}

function AddToCart(form, shoppingCart) {
    let productId = Number(form.data("id"));
    let itemName = form.data("name");
    let itemVendor = form.data("vendor");
    let itemImage = form.data("image");
    let itemSku = form.data("sku");
    let itemPrice = Number(form.data("price"));
    let quantityInput = form.find("input");
    let itemQuantity = Number(quantityInput.val());
    let itemText = form.find("textarea").val();
    let itemMeasurement = form.data("measurement");
    let itemOptions = productOptionsToJson(form);
    if (itemQuantity > 0) {
        let cartItem = shoppingCart.find((obj) => {
            return obj["id"] === productId;
        });
        if (!cartItem) {
            cartItem = {
                id: productId,
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
    } else {
        shoppingCart = shoppingCart.filter((obj) => {
            return obj["id"] !== productId;
        });
    }
    sessionStorage.setItem("shoppingCart", JSON.stringify(shoppingCart));
    return SyncShoppingCart();
}