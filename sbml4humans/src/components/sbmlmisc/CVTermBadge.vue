<template>
    <div class="d-flex mb-1">
        <div class="badge badge-success qualifier">{{ qualifier }}</div>
        <a :href="resource" target="_blank" class="badge badge-warning resource">{{
            resource
        }}</a>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";

export default defineComponent({
    props: {
        qualifier: {
            type: String,
            default: "",
        },
        resource: {
            type: String,
            default: "",
        },
    },
});
</script>

<style lang="scss" scoped>
.qualifier {
    border-radius: 5px 0 0 5px;
}

.resource {
    border-radius: 0px 5px 5px 0;
}
</style>
