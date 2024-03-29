import time
from copy import deepcopy
from random import randint


class Solution:
    RES_OPS = 3
    SCHED_OPS = 2

    SIMPLE_CONSTRAINT_FLAG = True

    # expects origin to be a solution for the same instance
    def __init__(self, instance_definition, origin=None):
        self.instance = instance_definition
        self.schedule = {}
        # use useful_res as starting point
        self.res_used_by_act = {x: self.instance.useful_res[x] for x in range(self.instance.nActs)}

        self.__generate_solution(origin)

    def evaluate(self):
        return self.schedule[self.instance.nActs - 1]

    def __generate_solution(self, origin=None):
        if origin is not None:
            self.schedule = origin.schedule
            self.res_used_by_act = origin.res_used_by_act
        else:
            while True:
                initial_schedule = self.__generate_initial_schedule()
                if self.__check_precedence_relations(initial_schedule):
                    self.schedule = initial_schedule
                    if self.check_for_hard_constraints(self.SIMPLE_CONSTRAINT_FLAG):
                        break
                else:
                    continue

        old_schedule = deepcopy(self.schedule)
        while True:
            self.schedule = old_schedule
            # randomize schedule
            self.schedule, randomizedActivities = self.__randomize_schedule(self.schedule)
            # randomize resources to work with schedule
            self.__generate_res_used_by_act(self.res_used_by_act, randomizedActivities)

            if self.check_for_hard_constraints(self.SIMPLE_CONSTRAINT_FLAG):
                break

    def __check_precedence_relations(self, schedule):
        for activity in range(self.instance.nPrecs):
            if not schedule[self.instance.pred[activity]] \
                   + self.instance.dur[self.instance.pred[activity]] \
                   <= schedule[self.instance.succ[activity]]:
                return False
        return True

    def __generate_initial_schedule(self):
        schedule = {0: 0}
        currently_used_acts = [0]

        t = 0
        for act in range(self.instance.nActs - 1):
            # add at least 1, but possibly more, depending on how long to go and how many activites were used
            res_schedule, res_currently_used_acts, used_act = self.__add_activity_randomly(currently_used_acts,
                                                                                           schedule, t)

            schedule = res_schedule
            currently_used_acts = res_currently_used_acts
            t += self.instance.dur[used_act]

        return schedule

    def __get_possible_activities(self, currently_used_acts, schedule, t):
        available_acts = []
        for act in range(self.instance.nActs):
            # are all this activities predecessors already there
            predecessors = self.instance.predecessors_by_activity[act]
            if all(x in currently_used_acts for x in predecessors) and act not in currently_used_acts:
                # are all predecessors done yet?
                if not [schedule[pred_act] + self.instance.dur[pred_act] for pred_act in predecessors if
                        schedule[pred_act] + self.instance.dur[pred_act] > t]:
                    available_acts.append(act)

        return list(set(available_acts))

    def __randomize_schedule(self, schedule):
        while True:
            new_schedule = deepcopy(schedule)
            changed_activities = []
            # change 3 activities
            for i in range(self.SCHED_OPS):
                random_activity = randint(0, self.instance.nActs - 1)
                random_activity_time = new_schedule[random_activity]
                # change the time within 5%
                t = randint(int(random_activity_time * 0.95), int(random_activity_time * 1.05))
                new_schedule[random_activity] = t
                changed_activities.append(random_activity)

            if self.__check_precedence_relations(new_schedule) \
                    and self.instance.maxt >= new_schedule[self.instance.nActs - 1] >= self.instance.mint:
                return new_schedule, changed_activities

    def __add_activity_randomly(self, currently_used_acts, schedule, t):
        available_activities = self.__get_possible_activities(currently_used_acts, schedule, t)

        if len(currently_used_acts) != self.instance.nActs:
            rand_activity_index = randint(0, len(available_activities) - 1)
        else:
            rand_activity_index = 0

        rand_activity = available_activities[rand_activity_index]

        schedule[rand_activity] = t
        currently_used_acts.append(rand_activity)
        del available_activities[rand_activity_index]

        return schedule, currently_used_acts, rand_activity

    def __generate_res_used_by_act(self, res_used_by_act_origin, activities_to_work_on):
        old_res_used_by_act_origin = deepcopy(res_used_by_act_origin)
        res_used_by_act_origin = deepcopy(res_used_by_act_origin)

        for activity in activities_to_work_on:
            for i in range(self.RES_OPS):
                operation = randint(1, 10)
                if len(res_used_by_act_origin[activity]) == 0:
                    break
                random_resource = randint(0, len(res_used_by_act_origin[activity]) - 1)
                if operation < 7:
                    del res_used_by_act_origin[activity][random_resource]
                elif operation < 9:
                    f = 0
                    while (random_resource not in self.instance.useful_res[activity] or
                           random_resource in self.res_used_by_act[activity]):

                        if f == 50:
                            break

                        random_resource = randint(0, self.instance.nResources - 1)
                        f += 1

                    res_used_by_act_origin[activity].append(random_resource)
                self.res_used_by_act = res_used_by_act_origin

            if not self.check_for_hard_constraints(self.SIMPLE_CONSTRAINT_FLAG):
                self.res_used_by_act = deepcopy(old_res_used_by_act_origin)
                res_used_by_act_origin = deepcopy(old_res_used_by_act_origin)
                continue

        return

    def check_for_hard_constraints(self, simpleConstraint=False):
        return self.__check_schedule_for_precedence_relation() and \
               self.__check_res_used_by_act_for_subset_of_useful_res() and \
               self.__check_if_skill_requirement_is_met(simpleConstraint) and \
               self.__check_if_no_resource_is_overlapping()

    def __check_schedule_for_precedence_relation(self):
        # constraint forall(i in PREC)((schedule[pred[i]] + dur[pred[i]]) <= schedule[succ[i]]);
        isValid = self.__check_precedence_relations(self.schedule)
        return isValid

    def __check_res_used_by_act_for_subset_of_useful_res(self):
        for act in range(self.instance.nActs):
            # all(x in currently_used_acts for x in predecessors)
            if not all(x in self.instance.useful_res[act] for x in self.res_used_by_act[act]):
                return False
        return True

    def __check_if_skill_requirement_is_met(self, simpleConstraint=False):
        for activity in range(self.instance.nActs):
            # old constraint
            if not self.__check_if_resources_fulfill_skills(activity):
                return False

            if simpleConstraint:
                continue

            # check if enough people are working on it
            if not self.__check_if_enough_resources_are_used(activity):
                return False

            if not self.__check_if_needed_skills_are_met(activity):
                return False

        return True

    def __check_if_needed_skills_are_met(self, activity):
        resources = self.res_used_by_act[activity]
        resource_values = {}

        # get resources for each amount of skills
        for resource in resources:
            value = 0
            for skill in range(self.instance.nSkills):
                if self.instance.mastery[resource][skill]:
                    value += 1

            if value not in resource_values:
                resource_values[value] = []

            resource_values[value].append(resource)

        left_skill_requirements = deepcopy(self.instance.sreq[activity])

        # do the obvious ones
        if 1 in resource_values:
            for resource in resource_values[1]:
                for skill in range(self.instance.nSkills):
                    if self.instance.mastery[resource][skill]:
                        left_skill_requirements[skill] -= 1

            # no longer relevant
            del resource_values[1]

        # now do the rest
        return self.__recursive_trying_of_skill_paths(resource_values, left_skill_requirements)

    def __recursive_trying_of_skill_paths(self, left_resources, skill_left):
        if self.__check_if_skill_left_is_empty(skill_left):
            return True

        if self.__check_if_left_resources_is_empty(left_resources):
            return False

        for skill_value in left_resources.keys():
            for resource in left_resources[skill_value]:
                for skill in range(self.instance.nSkills):
                    if self.instance.mastery[resource][skill]:
                        temp_left_resources = deepcopy(left_resources)
                        temp_left_resources[skill_value].remove(resource)

                        temp_skill_left = deepcopy(skill_left)
                        temp_skill_left[skill] -= 1

                        if self.__recursive_trying_of_skill_paths(temp_left_resources, temp_skill_left):
                            return True

        return False

    def __check_if_skill_left_is_empty(self, skill_left):
        for skill in range(self.instance.nSkills):
            if skill_left[skill] > 0:
                return False

        return True

    def __check_if_left_resources_is_empty(self, left_resources):
        for value in left_resources.keys():
            if len(left_resources[value]) > 0:
                return False

        return True

    def __check_if_enough_resources_are_used(self, activity):
        needed_skills = 0
        for skill in range(self.instance.nSkills):
            needed_skills += self.instance.sreq[activity][skill]
        return len(self.res_used_by_act[activity]) >= needed_skills

    def __check_if_resources_fulfill_skills(self, activity):
        for skill in range(self.instance.nSkills):
            skill_value = 0
            for res in self.res_used_by_act[activity]:
                if self.instance.mastery[res][skill]:
                    skill_value += 1

            if skill_value < self.instance.sreq[activity][skill]:
                return False

        return True

    # constraint forall(a1 in ACT, a2 in ACT where a1!=a2)
    # ((schedule[a1] <= schedule[a2] /\ schedule[a2] < (schedule[a1]+dur[a1]))
    # -> (res_used_by_act[a1] intersect res_used_by_act[a2] = {}));
    def __check_if_no_resource_is_overlapping(self):
        for act1 in range(self.instance.nActs):
            for act2 in range(self.instance.nActs):
                if act1 == act2:
                    continue

                if self.schedule[act1] <= self.schedule[act2] and \
                        (self.schedule[act2] < (self.schedule[act1] + self.instance.dur[act1])):
                    if set(self.res_used_by_act[act1]).intersection(set(self.res_used_by_act[act2])):
                        return False

        return True
