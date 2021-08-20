<template>
    <menubar :model="items">
        <template #start>
            <div style="display: flex">
                <img
                    alt="logo"
                    src="@/assets/images/sbmlutils-logo-60.png"
                    height="35"
                />
                <img
                    alt="logo"
                    src="@/assets/images/people.png"
                    height="35"
                />
                <span class="sbml4humans p-mx-3">SBML4Humans</span>
                <!--<InputText placeholder="Search in SBML" type="text" />-->

            </div>

        </template>
    </menubar>
</template>

<script lang="ts">
import { defineComponent } from "vue";

/**
 * Navbar component for providing main links in the application
 */
export default defineComponent({
    data() {
        return {
            items: [
                {
                   label:'Home',
                   icon:'pi pi-fw pi-home',
                   to: '/'
                },
                {
                   label:'Report issue',
                   icon:'pi pi-fw pi-pencil',
                   url:'https://github.com/matthiaskoenig/sbmlutils/issues/new/choose'
                },
                {
                   label:'Source',
                   icon:'pi pi-fw pi-github',
                   url:'https://github.com/matthiaskoenig/sbmlutils'
                }
             ]
        }
    }
});
</script>

<style lang="scss" scoped>
.sbml4humans {

    font-family: 'Roboto Slab', serif;
    font-size: 30px;
}

// FIXME: figure out how to put items right
//.p-menubar-list {
//   float: right;
//}
</style>
