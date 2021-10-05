<template>
    <strong
        ><code>{{ props.data.id }}</code></strong
    >
    <font-awesome-icon
        v-if="props.data.port != null"
        icon="plug"
        :title="props.data.port.pk.split(':')[1]"
        class="p-ml-1"
    />
</template>

<script>
import { defineComponent } from "@vue/runtime-core";
export default defineComponent({
    props: {
        props: {
            type: Object,
        },
    },
});
</script>

<style scoped></style>
