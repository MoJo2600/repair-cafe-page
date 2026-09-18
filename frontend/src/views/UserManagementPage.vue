<template>
    <v-container fluid class="pa-4">
        <v-row align="center" class="mb-4">
            <v-col>
                <h1 class="text-h5 font-weight-bold">Benutzerverwaltung</h1>
            </v-col>
            <v-col cols="auto">
                <v-btn color="primary" prepend-icon="mdi-account-plus" @click="openCreateDialog">
                    Neuer Benutzer
                </v-btn>
            </v-col>
        </v-row>

        <!-- Filter bar -->
        <v-row class="mb-2">
            <v-col cols="12" sm="4">
                <v-text-field v-model="search" prepend-inner-icon="mdi-magnify" label="Suchen…" density="compact"
                    clearable hide-details />
            </v-col>
            <v-col cols="12" sm="4">
                <v-select v-model="filterActive" :items="activeFilterOptions" label="Status" density="compact"
                    hide-details />
            </v-col>
        </v-row>

        <!-- Users table -->
        <v-card>
            <v-data-table :headers="headers" :items="filteredUsers" :loading="loading" item-value="id" hover
                @click:row="(_e: MouseEvent, { item }: { item: any }) => openEditDialog(item)">
                <!-- Active chip -->
                <template #item.is_active="{ item }">
                    <v-chip :color="item.is_active ? 'success' : 'error'" size="small" variant="tonal">
                        {{ item.is_active ? 'Aktiv' : 'Deaktiviert' }}
                    </v-chip>
                </template>

                <!-- Admin chip -->
                <template #item.is_admin="{ item }">
                    <v-chip v-if="item.is_admin" color="primary" size="small" variant="tonal">
                        Admin
                    </v-chip>
                    <span v-else class="text-medium-emphasis">—</span>
                </template>

                <!-- Full name -->
                <template #item.name="{ item }">
                    {{ item.vorname }} {{ item.nachname }}
                </template>

                <!-- Actions -->
                <template #item.actions="{ item }">
                    <v-btn icon="mdi-pencil" size="small" variant="text" density="compact"
                        @click.stop="openEditDialog(item)" />
                    <v-btn v-if="item.is_active" icon="mdi-account-off" size="small" variant="text" density="compact"
                        color="warning" :disabled="item.id === authStore.currentUser?.id" title="Benutzer deaktivieren"
                        @click.stop="confirmDeactivate(item)" />
                    <v-btn v-else icon="mdi-account-check" size="small" variant="text" density="compact" color="success"
                        title="Benutzer reaktivieren" @click.stop="reactivate(item)" />
                </template>
            </v-data-table>
        </v-card>

        <!-- Create / Edit dialog -->
        <v-dialog v-model="formDialog" max-width="520" persistent>
            <v-card>
                <v-card-title>{{ editingUser ? 'Benutzer bearbeiten' : 'Neuer Benutzer' }}</v-card-title>
                <v-card-text>
                    <v-alert v-if="formError" type="error" variant="tonal" density="compact" class="mb-4">
                        {{ formError }}
                    </v-alert>
                    <v-form ref="formRef" @submit.prevent="saveUser">
                        <v-row dense>
                            <v-col cols="12">
                                <v-text-field v-model="form.username" label="Benutzername *"
                                    :rules="[required]" autocomplete="off" />
                            </v-col>
                            <v-col cols="6">
                                <v-text-field v-model="form.vorname" label="Vorname *"
                                    :rules="[required]" />
                            </v-col>
                            <v-col cols="6">
                                <v-text-field v-model="form.nachname" label="Nachname *"
                                    :rules="[required]" />
                            </v-col>
                            <v-col cols="12">
                                <v-text-field v-model="form.email" label="E-Mail *"
                                    :rules="[required, emailRule]" type="email" autocomplete="off" />
                            </v-col>
                            <v-col cols="12">
                                <v-text-field v-model="form.password"
                                    :label="editingUser ? 'Neues Passwort (leer lassen = unverändert)' : 'Passwort *'"
                                    :type="showPassword ? 'text' : 'password'"
                                    :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                                    :rules="editingUser ? [minLen8IfSet] : [required, minLen8]"
                                    autocomplete="new-password" @click:append-inner="showPassword = !showPassword" />
                            </v-col>
                            <v-col cols="6">
                                <v-checkbox v-model="form.is_admin" label="Administrator" hide-details
                                    density="compact" />
                            </v-col>
                            <v-col v-if="editingUser" cols="6">
                                <v-checkbox v-model="form.is_active" label="Aktiv" hide-details density="compact" />
                            </v-col>
                        </v-row>
                    </v-form>
                </v-card-text>
                <v-card-actions>
                    <v-spacer />
                    <v-btn variant="text" @click="formDialog = false">Abbrechen</v-btn>
                    <v-btn color="primary" :loading="saving" @click="saveUser">Speichern</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Deactivate confirmation -->
        <v-dialog v-model="deactivateDialog" max-width="420">
            <v-card>
                <v-card-title>Benutzer deaktivieren</v-card-title>
                <v-card-text>
                    Benutzer <strong>{{ deactivateTarget?.username }}</strong> wirklich deaktivieren?
                    Der Benutzer kann sich danach nicht mehr anmelden.
                </v-card-text>
                <v-card-actions>
                    <v-spacer />
                    <v-btn variant="text" @click="deactivateDialog = false">Abbrechen</v-btn>
                    <v-btn color="warning" :loading="saving" @click="doDeactivate">Deaktivieren</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">
            {{ snackbarText }}
        </v-snackbar>
    </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { UserResponse } from "@/api/types";
import { useAuthStore } from "@/stores/authStore";

const authStore = useAuthStore();

// ── state ──────────────────────────────────────────────────────────────────
const users = ref<UserResponse[]>([]);
const loading = ref(false);
const saving = ref(false);
const search = ref("");
const filterActive = ref<"all" | "active" | "inactive">("active");

const formDialog = ref(false);
const deactivateDialog = ref(false);
const deactivateTarget = ref<UserResponse | null>(null);
const editingUser = ref<UserResponse | null>(null);
const formError = ref("");
const showPassword = ref(false);
const formRef = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null);

const snackbar = ref(false);
const snackbarText = ref("");
const snackbarColor = ref("success");

const emptyForm = () => ({
    username: "",
    vorname: "",
    nachname: "",
    email: "",
    password: "",
    is_admin: false,
    is_active: true,
});
const form = ref(emptyForm());

// ── table config ────────────────────────────────────────────────────────────
const headers = [
    { title: "Benutzername", key: "username" },
    { title: "Name", key: "name", sortable: false },
    { title: "E-Mail", key: "email" },
    { title: "Rolle", key: "is_admin", sortable: false },
    { title: "Status", key: "is_active", sortable: false },
    { title: "", key: "actions", sortable: false, align: "end" as const },
];

const activeFilterOptions = [
    { title: "Alle", value: "all" },
    { title: "Aktiv", value: "active" },
    { title: "Deaktiviert", value: "inactive" },
];

// ── computed ────────────────────────────────────────────────────────────────
const filteredUsers = computed(() => {
    let list = users.value;
    if (filterActive.value === "active") list = list.filter((u) => u.is_active);
    else if (filterActive.value === "inactive") list = list.filter((u) => !u.is_active);

    if (search.value.trim()) {
        const q = search.value.toLowerCase();
        list = list.filter(
            (u) =>
                u.username.toLowerCase().includes(q) ||
                (u.vorname ?? "").toLowerCase().includes(q) ||
                (u.nachname ?? "").toLowerCase().includes(q) ||
                u.email.toLowerCase().includes(q)
        );
    }
    return list;
});

// ── validation rules ────────────────────────────────────────────────────────
const required = (v: string) => !!v?.trim() || "Pflichtfeld";
const emailRule = (v: string) => /.+@.+\..+/.test(v) || "Ungültige E-Mail";
const minLen8 = (v: string) => v?.length >= 8 || "Mindestens 8 Zeichen";
const minLen8IfSet = (v: string) => !v || v.length >= 8 || "Mindestens 8 Zeichen";

// ── helpers ─────────────────────────────────────────────────────────────────
function showMsg(text: string, color = "success") {
    snackbarText.value = text;
    snackbarColor.value = color;
    snackbar.value = true;
}

async function fetchUsers() {
    loading.value = true;
    try {
        const res = await fetch("/api/users", { credentials: "include" });
        const data = await res.json();
        users.value = data.data ?? [];
    } finally {
        loading.value = false;
    }
}

// ── dialog helpers ──────────────────────────────────────────────────────────
function openCreateDialog() {
    editingUser.value = null;
    form.value = emptyForm();
    formError.value = "";
    showPassword.value = false;
    formDialog.value = true;
}

function openEditDialog(user: UserResponse) {
    editingUser.value = user;
    form.value = {
        username: user.username,
        vorname: user.vorname ?? "",
        nachname: user.nachname ?? "",
        email: user.email,
        password: "",
        is_admin: user.is_admin,
        is_active: user.is_active,
    };
    formError.value = "";
    showPassword.value = false;
    formDialog.value = true;
}

// ── CRUD ────────────────────────────────────────────────────────────────────
async function saveUser() {
    const { valid } = await formRef.value!.validate();
    if (!valid) return;

    saving.value = true;
    formError.value = "";

    try {
        const payload: Record<string, unknown> = {
            username: form.value.username,
            vorname: form.value.vorname,
            nachname: form.value.nachname,
            email: form.value.email,
            is_admin: form.value.is_admin,
        };
        if (editingUser.value) {
            payload.is_active = form.value.is_active;
            if (form.value.password) payload.password = form.value.password;
        } else {
            payload.password = form.value.password;
        }

        const url = editingUser.value
            ? `/api/users/${editingUser.value.id}`
            : "/api/users";
        const method = editingUser.value ? "PUT" : "POST";

        const res = await fetch(url, {
            method,
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (!res.ok) {
            formError.value = data.error ?? "Fehler beim Speichern";
            return;
        }

        formDialog.value = false;
        await fetchUsers();
        showMsg(editingUser.value ? "Benutzer aktualisiert" : "Benutzer erstellt");
    } finally {
        saving.value = false;
    }
}

function confirmDeactivate(user: UserResponse) {
    deactivateTarget.value = user;
    deactivateDialog.value = true;
}

async function doDeactivate() {
    if (!deactivateTarget.value) return;
    saving.value = true;
    try {
        const res = await fetch(`/api/users/${deactivateTarget.value.id}`, {
            method: "DELETE",
            credentials: "include",
        });
        if (res.ok) {
            deactivateDialog.value = false;
            await fetchUsers();
            showMsg("Benutzer deaktiviert", "warning");
        } else {
            const d = await res.json();
            showMsg(d.error ?? "Fehler", "error");
        }
    } finally {
        saving.value = false;
    }
}

async function reactivate(user: UserResponse) {
    saving.value = true;
    try {
        const res = await fetch(`/api/users/${user.id}`, {
            method: "PUT",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: true }),
        });
        if (res.ok) {
            await fetchUsers();
            showMsg("Benutzer reaktiviert");
        } else {
            const d = await res.json();
            showMsg(d.error ?? "Fehler", "error");
        }
    } finally {
        saving.value = false;
    }
}

onMounted(fetchUsers);
</script>
