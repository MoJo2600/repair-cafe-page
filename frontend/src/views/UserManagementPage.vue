<template>
    <v-container fluid class="pa-4">
        <PageHeader title="Benutzerverwaltung">
            <template #actions>
                <v-btn color="primary" variant="flat" prepend-icon="mdi-account-plus" @click="openCreateDialog">
                    Neuer Benutzer
                </v-btn>
            </template>
        </PageHeader>

        <!-- Filter bar -->
        <v-row class="mb-2">
            <v-col cols="12" sm="4">
                <v-text-field
v-model="search" prepend-inner-icon="mdi-magnify" label="Suchen…" density="compact"
                    clearable hide-details />
            </v-col>
            <v-col cols="12" sm="4">
                <v-select
v-model="filterActive" :items="activeFilterOptions" label="Status" density="compact"
                    hide-details />
            </v-col>
        </v-row>

        <!-- Users table -->
        <v-card>
            <v-data-table
:headers="headers" :items="filteredUsers" :loading="loading" item-value="id" hover
                @click:row="(_e: MouseEvent, { item }: { item: any }) => openEditDialog(item)">
                <!-- Active chip -->
                <template #item.is_active="{ item }">
                    <StatusChip v-if="item.is_active" label="Aktiv" color="success" icon="mdi-check" />
                    <StatusChip v-else label="Deaktiviert" icon="mdi-cancel" />
                </template>

                <!-- Admin chip -->
                <template #item.is_admin="{ item }">
                    <StatusChip v-if="item.is_admin" label="Admin" icon="mdi-shield-account" />
                    <span v-else class="text-medium-emphasis">–</span>
                </template>

                <!-- Full name -->
                <template #item.name="{ item }">
                    {{ personName(item) }}
                </template>

                <!-- Actions -->
                <template #item.actions="{ item }">
                    <v-btn
icon="mdi-pencil" size="small" variant="text" density="compact"
                        @click.stop="openEditDialog(item)" />
                    <v-btn
v-if="item.is_active" icon="mdi-account-off" size="small" variant="text" density="compact"
                        color="error" :disabled="item.id === authStore.currentUser?.id" title="Benutzer deaktivieren"
                        @click.stop="confirmDeactivate(item)" />
                    <v-btn
v-else icon="mdi-account-check" size="small" variant="text" density="compact" color="success"
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
                        <v-row density="compact">
                            <v-col cols="12">
                                <v-text-field
v-model="form.username" label="Benutzername *"
                                    :rules="[required]" autocomplete="off" />
                            </v-col>
                            <v-col cols="6">
                                <v-text-field
v-model="form.vorname" label="Vorname *"
                                    :rules="[required]" />
                            </v-col>
                            <v-col cols="6">
                                <v-text-field
v-model="form.nachname" label="Nachname *"
                                    :rules="[required]" />
                            </v-col>
                            <v-col cols="12">
                                <v-text-field
v-model="form.email" label="E-Mail *"
                                    :rules="[required, emailRule]" type="email" autocomplete="off" />
                            </v-col>
                            <v-col cols="12">
                                <v-text-field
v-model="form.password"
                                    :label="editingUser ? 'Neues Passwort (leer lassen = unverändert)' : 'Passwort *'"
                                    :type="showPassword ? 'text' : 'password'"
                                    :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                                    :rules="editingUser ? [minLen8IfSet] : [required, minLen8]"
                                    autocomplete="new-password" @click:append-inner="showPassword = !showPassword" />
                            </v-col>
                            <v-col cols="6">
                                <v-checkbox
v-model="form.is_admin" label="Administrator" hide-details
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

    </v-container>
</template>

<script setup lang="ts">
import PageHeader from "@/components/ui/PageHeader.vue";
import StatusChip from "@/components/ui/StatusChip.vue";
import { personName } from "@/utils/person";
import { computed, onMounted, ref } from "vue";
import type { VForm } from "vuetify/components";
import { api } from "@/api/client";
import { errorMessage } from "@/utils/errors";
import type { UserResponse } from "@/api/types";
import { useAuthStore } from "@/stores/authStore";
import { useToast } from "@/composables/useToast";

const toast = useToast();

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
const formRef = ref<InstanceType<typeof VForm> | null>(null);


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
async function fetchUsers() {
    loading.value = true;
    try {
        const res = await api.listUsers();
        users.value = res.data;
    } catch (err) {
        toast.error(errorMessage(err, "Fehler beim Laden der Benutzer"));
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
        const fields = {
            username: form.value.username,
            vorname: form.value.vorname,
            nachname: form.value.nachname,
            email: form.value.email,
            is_admin: form.value.is_admin,
        };
        if (editingUser.value) {
            await api.updateUser(
                { userId: editingUser.value.id },
                {
                    ...fields,
                    is_active: form.value.is_active,
                    ...(form.value.password ? { password: form.value.password } : {}),
                },
            );
        } else {
            await api.createUser({ ...fields, password: form.value.password });
        }

        formDialog.value = false;
        await fetchUsers();
        toast.success(editingUser.value ? "Benutzer aktualisiert" : "Benutzer erstellt");
    } catch (err) {
        formError.value = errorMessage(err, "Fehler beim Speichern");
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
        await api.deactivateUser({ userId: deactivateTarget.value.id });
        deactivateDialog.value = false;
        await fetchUsers();
        toast.warning("Benutzer deaktiviert");
    } catch (err) {
        toast.error(errorMessage(err, "Fehler"));
    } finally {
        saving.value = false;
    }
}

async function reactivate(user: UserResponse) {
    saving.value = true;
    try {
        await api.updateUser({ userId: user.id }, { is_active: true });
        await fetchUsers();
        toast.success("Benutzer reaktiviert");
    } catch (err) {
        toast.error(errorMessage(err, "Fehler"));
    } finally {
        saving.value = false;
    }
}

onMounted(fetchUsers);
</script>
