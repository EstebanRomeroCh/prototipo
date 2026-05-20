// ==============================
// CONFIGURACIÓN INICIAL
// ==============================
let productos = [];
let categorias = [];
let subcategorias = [];
let unidades = [];
let editandoProducto = null;

const formProducto = document.getElementById('formProducto');
const tablaProductos = document.getElementById('tablaProductos').querySelector('tbody');
const buscadorProductos = document.getElementById('buscadorProductos');

const API_PRODUCTOS = '/api/productos';
const API_CATEGORIAS = '/api/categorias';
const API_SUBCATEGORIAS = '/api/subcategorias';
const API_UNIDADES = '/api/unidades';

// ==============================
// FUNCIÓN DE SIMILITUD
// ==============================
function es_similar(a, b) {
    return a.trim().toLowerCase() === b.trim().toLowerCase();
}

// ==============================
// FORMATEO DE NÚMEROS
// ==============================
function formatNumber(value) {
    if (value === null || value === undefined || value === '') return '';

    const num = Number(value);
    if (Number.isNaN(num)) return value; // por si llega algo raro

    // Si es entero, sin decimales: 50
    if (Number.isInteger(num)) return num.toString();

    // Si tiene decimales, máximo 3 y sin ceros basura: 0.250 -> 0.25
    return num.toFixed(3).replace(/\.?0+$/, '');
}

// ==============================
// CARGAR CATEGORÍAS Y SUBCATEGORÍAS
// ==============================
async function cargarCategoriasYSubcategorias() {
    try {
        const resCat = await fetch(API_CATEGORIAS);
        categorias = await resCat.json();

        const selectCrear = document.getElementById('categoriaSelect');
        const selectModalCat = document.getElementById('categoriaProductoModal');

        selectCrear.innerHTML = '<option value="">Selecciona una categoría</option>';
        selectModalCat.innerHTML = '<option value="">Selecciona una categoría</option>';

        categorias.forEach(cat => {
            // Se asume respuesta tipo [id, nombre, ...]
            selectCrear.innerHTML += `<option value="${cat[0]}">${cat[1]}</option>`;
            selectModalCat.innerHTML += `<option value="${cat[0]}">${cat[1]}</option>`;
        });

        // Evento formulario crear
        selectCrear.addEventListener('change', async () => {
            const id_categoria = selectCrear.value;
            const selectSub = document.getElementById('subcategoriaSelect');
            selectSub.innerHTML = '';

            if (!id_categoria) {
                selectSub.innerHTML = '<option value="">Selecciona una categoría primero</option>';
                selectSub.disabled = true;
                return;
            }

            const resSub = await fetch(API_SUBCATEGORIAS);
            const todasSub = await resSub.json();
            const subRelacionadas = todasSub.filter(
                sub => sub[3].toString() === id_categoria.toString()
            );

            if (subRelacionadas.length > 0) {
                subRelacionadas.forEach(sub => {
                    selectSub.innerHTML += `<option value="${sub[0]}">${sub[1]}</option>`;
                });
                selectSub.disabled = false;
            } else {
                // 🔴 AQUÍ ESTABA EL ERROR: inner.innerHTML
                selectSub.innerHTML = '<option value="">No hay subcategorías</option>';
                selectSub.disabled = true;
            }
        });

        // Evento modal editar
        selectModalCat.addEventListener('change', async () => {
            const id_categoria = selectModalCat.value;
            const selectSubModal = document.getElementById('subcategoriaProductoModal');
            selectSubModal.innerHTML = '';

            if (!id_categoria) {
                selectSubModal.innerHTML = '<option value="">Selecciona una categoría primero</option>';
                selectSubModal.disabled = true;
                return;
            }

            const resSub = await fetch(API_SUBCATEGORIAS);
            const todasSub = await resSub.json();
            const subRelacionadas = todasSub.filter(
                sub => sub[3].toString() === id_categoria.toString()
            );

            if (subRelacionadas.length > 0) {
                subRelacionadas.forEach(sub => {
                    selectSubModal.innerHTML += `<option value="${sub[0]}">${sub[1]}</option>`;
                });
                selectSubModal.disabled = false;
            } else {
                selectSubModal.innerHTML = '<option value="">No hay subcategorías</option>';
                selectSubModal.disabled = true;
            }
        });

    } catch (error) {
        console.error('Error cargando categorías y subcategorías:', error);
        swal("Error", "No se pudieron cargar las categorías y subcategorías", "error");
    }
}

// ==============================
// CARGAR UNIDADES
// ==============================
async function cargarUnidades() {
    try {
        fetch('/api/unidades/activas')
            .then(res => res.json())
            .then(unids => {

                unidades = unids;

                const select = document.getElementById('selectUnidad');
                select.innerHTML = '<option value="">Seleccione...</option>';

                unids.forEach(u => {
                    const opt = document.createElement("option");
                    opt.value = u.id_unidad;
                    opt.textContent = u.nombre;
                    select.appendChild(opt);
                });

                const selectModal = document.getElementById('selectUnidadModal');
                if (selectModal) {
                    selectModal.innerHTML = '<option value="">Seleccione...</option>';
                    unids.forEach(u => {
                        const opt = document.createElement("option");
                        opt.value = u.id_unidad;
                        opt.textContent = u.nombre;
                        selectModal.appendChild(opt);
                    });
                }
            });

    } catch (error) {
        console.error("Error cargarUnidades:", error);
    }
}

// ==============================
// CARGAR PRODUCTOS
// ==============================
// ==============================
// CARGAR PRODUCTOS
// ==============================
async function cargarProductos() {
    try {
        const res = await fetch(API_PRODUCTOS);
        const data = await res.json();

        productos = data.map(p => {
            const stock = Number(p.stock_minimo);
            const pesoUnit = Number(p.peso_unitario);
            const pesoKg = Number(p.peso_kg);

            return {
                id_producto: p.id_producto,
                nombre: p.nombre,
                stock_minimo: Number.isNaN(stock) ? p.stock_minimo : stock,
                peso_unitario: Number.isNaN(pesoUnit) ? p.peso_unitario : pesoUnit,
                peso_kg: Number.isNaN(pesoKg) ? p.peso_kg : pesoKg,
                id_unidad: p.id_unidad,
                descripcion: p.descripcion,
                id_categoria: p.id_categoria,
                id_subcategoria: p.id_subcategoria,
                categoria: p.categoria,
                subcategoria: p.subcategoria,
                unidad_medida: p.unidad_medida || "Sin unidad"
            };
        });

        tablaProductos.innerHTML = '';

        productos.forEach(prod => {
            const fila = `
                <tr data-id="${prod.id_producto}">
                    <td>${prod.id_producto}</td>
                    <td class="col-nombre">${prod.nombre}</td>
                    <td>${formatNumber(prod.stock_minimo)}</td>
                    <td>${formatNumber(prod.peso_unitario)} (${formatNumber(prod.peso_kg)} kg)</td>
                    <td>${prod.unidad_medida}</td>
                    <td>${prod.descripcion}</td>
                    <td>
                        <button class="btn btn-sm btn-success me-2" onclick="abrirModalEditarProducto(${prod.id_producto})">
                            <i class="bi bi-pencil-fill"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="eliminarProducto(${prod.id_producto})">
                            <i class="bi bi-trash-fill"></i>
                        </button>
                    </td>
                </tr>
            `;
            tablaProductos.insertAdjacentHTML("beforeend", fila);
        });

    } catch (error) {
        console.error('Error cargando productos:', error);
        swal("Error", "No se pudieron cargar los productos", "error");
    }
}


// ==============================
// BUSCADOR DE PRODUCTOS
// ==============================
buscadorProductos.addEventListener('input', () => {
    const texto = buscadorProductos.value.toLowerCase().trim();

    Array.from(tablaProductos.rows).forEach(row => {
        const nombre = row.querySelector('.col-nombre').textContent.toLowerCase();
        const descripcion = row.children[5].textContent.toLowerCase();
        const peso = row.children[3].textContent.toLowerCase();
        const unidad = row.children[4].textContent.toLowerCase();

        const coincide =
            nombre.includes(texto) ||
            descripcion.includes(texto) ||
            peso.includes(texto) ||
            unidad.includes(texto);

        row.style.display = coincide ? '' : 'none';
    });
});

// ==============================
// CREAR PRODUCTO
// ==============================
formProducto.addEventListener('submit', async function (e) {
    e.preventDefault();

    const nombre = document.getElementById('productoSelect').value.trim();
    const id_categoria = document.getElementById('categoriaSelect').value;
    const id_subcategoria = document.getElementById('subcategoriaSelect').value;
    const stock_minimo = document.getElementById('cantidadProducto').value;
    const peso_unitario = document.getElementById('pesoUnitarioInput').value;
    const id_unidad = document.getElementById('selectUnidad').value;
    const descripcion = document.getElementById('descripcionProducto').value.trim();

    if (!nombre || !id_categoria || !id_subcategoria || !stock_minimo || !peso_unitario || !id_unidad) {
        swal("Error", "Todos los campos son obligatorios", "error");
        return;
    }

    if (productos.some(p => es_similar(p.nombre, nombre))) {
        swal("Error", "Ya existe un producto con nombre similar", "error");
        return;
    }

    try {
        const res = await fetch(API_PRODUCTOS, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nombre,
                id_categoria,
                id_subcategoria,
                stock_minimo,
                peso_unitario,
                id_unidad,
                descripcion
            })
        });

        const data = await res.json();

        if (res.ok && data.success) {
            await cargarProductos();
            formProducto.reset();
            swal("Éxito", "Producto creado correctamente", "success");
        } else {
            swal("Error", data.message || "No se pudo crear el producto", "error");
        }
    } catch (error) {
        console.error('Error creando producto:', error);
        swal("Error", "No se pudo crear el producto", "error");
    }
});

// ==============================
// MODAL EDITAR PRODUCTO
// ==============================
async function abrirModalEditarProducto(id) {
    try {
        const producto = productos.find(p => p.id_producto == id);
        if (!producto) {
            swal("Error", "Producto no encontrado en memoria", "error");
            return;
        }

        document.getElementById('idProductoModal').value = producto.id_producto;
        document.getElementById('nombreProductoModal').value = producto.nombre;
        document.getElementById('nombreStockModal').value = producto.stock_minimo;
        document.getElementById('pesoUnitarioModal').value = producto.peso_unitario;
        document.getElementById('descripcionProductoModal').value = producto.descripcion;
        document.getElementById('categoriaProductoModal').value = producto.id_categoria;

        const event = new Event('change');
        document.getElementById('categoriaProductoModal').dispatchEvent(event);

        setTimeout(() => {
            document.getElementById('subcategoriaProductoModal').value = producto.id_subcategoria;
        }, 150);

        await cargarUnidades();
        document.getElementById('selectUnidadModal').value = producto.id_unidad;

        editandoProducto = document.querySelector(`tr[data-id="${id}"]`);

        const modal = new bootstrap.Modal(document.getElementById('modalActualizarProducto'));
        modal.show();

    } catch (error) {
        console.error('Error cargando producto:', error);
        swal("Error", "No se pudo cargar el producto", "error");
    }
}

// ==============================
// ACTUALIZAR PRODUCTO
// ==============================
document.getElementById('formActualizarProducto').addEventListener('submit', async function (e) {
    e.preventDefault();

    const id = document.getElementById('idProductoModal').value;
    const nombre = document.getElementById('nombreProductoModal').value.trim();
    const id_categoria = document.getElementById('categoriaProductoModal').value;
    const id_subcategoria = document.getElementById('subcategoriaProductoModal').value;
    const stock_minimo = document.getElementById('nombreStockModal').value;
    const peso_unitario = document.getElementById('pesoUnitarioModal').value;
    const descripcion = document.getElementById('descripcionProductoModal').value.trim();
    const id_unidad = document.getElementById('selectUnidadModal').value;

    if (!nombre || !id_categoria || !id_subcategoria || !stock_minimo || !peso_unitario || !id_unidad) {
        swal("Error", "Todos los campos son obligatorios", "error");
        return;
    }

    if (productos.some(p => p.id_producto != id && es_similar(p.nombre, nombre))) {
        swal("Error", "Ya existe un producto con nombre similar", "error");
        return;
    }

    try {
        const res = await fetch(`${API_PRODUCTOS}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nombre,
                id_categoria,
                id_subcategoria,
                stock_minimo,
                peso_unitario,
                id_unidad,
                descripcion
            })
        });

        const data = await res.json();

        if (res.ok) {
            await cargarProductos();
            swal("Éxito", "Producto actualizado correctamente", "success");
        } else {
            swal("Error", data.message || "No se pudo actualizar el producto", "error");
        }
    } catch (error) {
        console.error('Error actualizando producto:', error);
        swal("Error", "No se pudo actualizar el producto", "error");
    }
});

// ==============================
// ELIMINAR PRODUCTO
// ==============================
async function eliminarProducto(id) {

    const confirmar = await swal({
        title: "¿Estás seguro?",
        text: "Una vez eliminado, no podrás recuperarlo",
        icon: "warning",
        buttons: true,
        dangerMode: true,
    });

    if (!confirmar) return;

    try {
        const res = await fetch(`${API_PRODUCTOS}/${id}`, { method: 'DELETE' });
        const data = await res.json();

        if (res.ok && data.success) {
            productos = productos.filter(p => p.id_producto != id);
            await cargarProductos();
            swal("Éxito", "Producto eliminado correctamente", "success");
        } else {
            swal("Error", data.message || "No se pudo eliminar el producto", "error");
        }
    } catch (error) {
        console.error('Error eliminando producto:', error);
        swal("Error", "No se pudo eliminar el producto", "error");
    }
}

// ==============================
// INICIALIZACIÓN
// ==============================
document.addEventListener('DOMContentLoaded', async () => {
    await cargarCategoriasYSubcategorias();
    await cargarUnidades();
    await cargarProductos();
});
