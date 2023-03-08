function GetShoppingCart() {
    let shoppingCart = JSON.parse(sessionStorage.getItem("shoppingCart") || "[]");
    if (!Array.isArray(shoppingCart)) {
        console.error("Invalid shopping cart data:", shoppingCart);
        return [];
    }
    shoppingCart = shoppingCart.filter(Boolean);
    sessionStorage.setItem("shoppingCart", JSON.stringify(shoppingCart));
    return shoppingCart;
}


function SetInCartText(shoppingCart = null) {
    if (!shoppingCart)
        shoppingCart = GetShoppingCart();
    else
        shoppingCart = shoppingCart.filter(Boolean);
    const numItems = shoppingCart.length;
    const inCartItems = document.getElementById("inCartItems");
    if (numItems > 0) {
        const totalPrice = shoppingCart.reduce((total, item) => total + (item.price || 0) * (item.quantity || 0), 0);
        inCartItems.textContent = `${numItems} позиции на сумму ${totalPrice.toFixed(2)}`;
    } else {
        inCartItems.textContent = "";
    }
}


function PopulateProductQuantities() {
    const cartItems = GetShoppingCart();
    for (const item of cartItems) {
        const productId = item.id;
        const input = document.querySelector(`#product${productId} input`);
        const plusSign = document.querySelector(`#product${productId} input+span`);

        if (input) {
            const prevValue = Number(input.value);
            input.value = prevValue + item.quantity;
            input.classList.add('border-success');
            plusSign.classList.remove('d-none');
        }
    }
}

function HandleAddToCart(event) {
    const button = event.currentTarget;
    const itemPos = Number(button.dataset.pos);
    const modal = button.closest('.modal');
    AddToCart(modal, itemPos);
    SetInCartText();
}

function HandleProductModalChangeClone(event) {
    event.preventDefault();

    const currentClone = event.currentTarget;
    const itemPos = Number(currentClone.value);

    const modal = currentClone.closest('.modal');
    SyncProductModal(modal, itemPos);

    const addToCartButtons = modal.querySelectorAll(".addToCart");
    addToCartButtons[1].dataset.pos = itemPos;
}


function PopulateProduct(item, index) {
    if (!item) {
        return;
    }
    const content = document.querySelector('#cartItemTemplate').cloneNode(true);
    const sku = content.querySelector('#productSkuTemplate');
    const name = content.querySelector('#productNameTemplate');
    const text = content.querySelector('#productTextTemplate');
    const image = content.querySelector('#productImageTemplate');
    const vendor = content.querySelector('#productVendorTemplate');
    const price = content.querySelector('#productPriceTemplate');
    const product = content.querySelector('#productIdTemplate');
    const quantity = content.querySelector('#productQuantityTemplate');
    const measurement = content.querySelector('#productMeasurementTemplate');
    const options = content.querySelector('#productOptionsTemplate');
    const optionsValues = content.querySelector('#productOptionsValuesTemplate');
    const textValue = content.querySelector('#productTextValueTemplate');

    content.removeAttribute('id');
    sku.removeAttribute('id');
    name.removeAttribute('id');
    text.removeAttribute('id');
    image.removeAttribute('id');
    vendor.removeAttribute('id');
    price.removeAttribute('id');
    product.removeAttribute('id');
    quantity.removeAttribute('id');
    measurement.removeAttribute('id');
    options.removeAttribute('id');
    optionsValues.removeAttribute('id');
    textValue.removeAttribute('id');

    content.dataset.id = item.id;
    content.dataset.pos = index;
    content.dataset.cost = Number(item.price) * Number(item.quantity);

    sku.textContent = item.sku;
    name.textContent = item.name;
    if (item.text) {
        text.value = item.text;
        textValue.textContent = item.text;
        let parentRow = textValue.parentNode;
        while (parentRow && !parentRow.classList.contains('row')) {
            parentRow = parentRow.parentNode;
        }
        if (parentRow) {
            parentRow.classList.remove('d-none');
        }
    }
    if (item.image) {
        image.setAttribute('src', item.image);
    }
    vendor.textContent = item.vendor;
    price.textContent = item.price.toFixed(2);
    product.value = item.id;
    quantity.value = item.quantity;
    measurement.textContent = item.measurement;
    if (item.options) {
        options.value = JSON.stringify(item.options);
        const optionsKeys = Object.keys(item.options);
        const optionsValuesArr = optionsKeys.map(key => `${key}: <strong>${item.options[key]}</strong>`);
        optionsValues.innerHTML = optionsValuesArr.join(', ');
        optionsValues.closest('.row').classList.remove('d-none')
    }
    text.setAttribute('name', text.getAttribute('name').replace('_', index));
    product.setAttribute('name', product.getAttribute('name').replace('_', index));
    quantity.setAttribute('name', quantity.getAttribute('name').replace('_', index));
    options.setAttribute('name', options.getAttribute('name').replace('_', index));
    document.querySelector('#shoppingCartItems').appendChild(content);
}

function productOptionsToJson(form) {
    let formData = {};
    let selectElements = form.querySelectorAll('select.productOption');
    const numElements = selectElements.length;
    for (let i = 0; i < numElements; i++) {
        let selected = selectElements[i].querySelector('option:checked');
        let name = selectElements[i].dataset.name;
        if (!selected.disabled) {
            formData[name] = selected.value;
        }
    }
    return formData;
}

function AddToCart(form, itemPos = null) {

    const shoppingCart = GetShoppingCart();
    const productId = Number(form.dataset.id);
    const quantityInput = form.querySelector("input");
    const itemQuantity = Number(quantityInput.value);
    const itemText = form.querySelector("textarea").value;
    const itemOptions = productOptionsToJson(form);

    if (itemQuantity > 0) {
        let item = {};
        if (Number.isInteger(itemPos))
            item = shoppingCart[itemPos];
        else {
            item = {
                id: productId,
                name: form.dataset.name,
                sku: form.dataset.sku,
                price: Number(form.dataset.price),
                vendor: form.dataset.vendor,
                image: form.dataset.image,
                measurement: form.dataset.measurement
            };
            shoppingCart.push(item);
        }

        if (itemText) {
            item.text = itemText;
        }

        if (itemOptions) {
            item.options = itemOptions;
        }

        item.quantity = itemQuantity;
    } else {
        if (Number.isInteger(itemPos))
            shoppingCart.splice(itemPos, 1);
    }

    let productQuantityInput = document.querySelector(`#product${productId} input`);
    const totalQuantity = shoppingCart.reduce(function (acc, i) {
        if (i.id == productId)
            acc += i.quantity;
        return acc;
    }, 0);
    const plusSign = document.querySelector(`#product${productId} input+span`);
    if (totalQuantity > 0) {
        productQuantityInput.value = totalQuantity;
        productQuantityInput.classList.add("border-success");
        plusSign.classList.remove("d-none");
    } else {
        productQuantityInput.value = "";
        productQuantityInput.classList.remove("border-success");
        plusSign.classList.add("d-none");
    }

    sessionStorage.setItem("shoppingCart", JSON.stringify(shoppingCart));
}


function SyncProductModal(form, itemPos) {

    const shoppingCart = GetShoppingCart();
    const item = shoppingCart[itemPos];

    let quantityInput = form.querySelector("input");
    quantityInput.value = item.quantity;
    quantityInput.focus();

    let textInput = form.querySelector("textarea");
    textInput.value = item.text || '';

    form.querySelectorAll('select.productOption').forEach((select) => {
        const name = select.getAttribute("data-name");
        if (name in item.options)
            select.value = item.options[name];
        else
            select.value = 0;
        select.dispatchEvent(new Event('change'));
    });
}

function SyncCartModal(form, item) {


    const descriptionModalLabel = document.getElementById('descriptionModalLabel');
    descriptionModalLabel.textContent = item.name;

    const descriptionModalProductMeasurement = document.getElementById('descriptionModalProductMeasurement');
    descriptionModalProductMeasurement.textContent = item.measurement;

    const quantityInput = document.getElementById('descriptionModalProductQuantity');
    quantityInput.value = item.quantity;
    quantityInput.focus();

    const textInput = document.getElementById('descriptionModalProductText');
    textInput.value = item.text || '';

    const descriptionModalProductOptions = document.getElementById("descriptionModalProductOptions");
    descriptionModalProductOptions.innerHTML = "";
    let content = document.createDocumentFragment();
    const optionsKeys = Object.keys(item.options);
    optionsKeys.forEach((key) => {
        const row = document.createElement('div');
        row.classList.add('mb-3');
        const label = document.createElement('lable');
        label.classList.add('form-label');
        label.textContent = key;
        const input = document.createElement('input');
        input.classList.add('form-control');
        input.value = item.options[key];
        input.setAttribute('readonly', 'true');
        input.setAttribute('disabled', 'true');
        input.setAttribute('type', 'text');
        row.appendChild(label);
        row.appendChild(input);
        content.appendChild(row);
    });
    descriptionModalProductOptions.appendChild(content);

    const image = form.querySelector('img');
    if (item.image)
        image.setAttribute("src", item.image);
    else
        image.setAttribute("src", "");
}

function CheckProjectAndSiteSet(selectProjectSiteCallback) {
    const projectId = Number(sessionStorage.getItem("project_id"));
    const siteId = Number(sessionStorage.getItem("site_id"));
    const siteName = sessionStorage.getItem("site_name");
    const projectName = sessionStorage.getItem("project_name");
    const siteProjectSelect = document.querySelector(".siteProjectSelect");
    if (!projectId || !siteId || !siteName || !projectName)
        selectProjectSiteCallback();
    else {
        document.querySelector("#projectName").textContent = projectName;
        document.querySelector("#siteName").textContent = siteName;
    }
    siteProjectSelect.addEventListener("click", function () {
        sessionStorage.removeItem("project_id");
        sessionStorage.removeItem("project_name");
        sessionStorage.removeItem("site_id");
        sessionStorage.removeItem("site_name");
        selectProjectSiteCallback();
    });
    return [projectId, siteId, siteName, projectName];
}
