<template>
    <strong
        ><code>{{ data.id }}</code></strong
    >
    <font-awesome-icon
        v-if="data.port != null"
        icon="plug"
        :title="data.port.pk.split(':')[1]"
        class="p-ml-1"
    />
</template>

<script>
import { defineComponent } from "@vue/runtime-core";
export default defineComponent({
    props: {
        data: {
            type: Object,
        },
    },
});
</script>

<style scoped></style>
